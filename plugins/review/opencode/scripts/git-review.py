#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
git-review.py — аннотационное ревью diff-файла через $EDITOR.

Сценарий:
1) генерируем diff (git diff / git diff --cached / git diff <ref>...HEAD)
2) пишем diff во временный файл
3) открываем файл в $EDITOR
4) после закрытия редактора:
   - если файл не изменился → ничего не печатаем (exit 0)
   - если изменился → печатаем unified diff "что пользователь добавил/поменял" (exit 0)

ВАЖНО:
- пользователь редактирует НЕ исходники, а diff-файл.
- изменения diff-файла трактуются как замечания/аннотации для агента.

Это заготовка под ваш workflow: при желании можно добавить интеграции с tmux/kitty/wezterm и т.п.
"""

from __future__ import annotations

import argparse
import difflib
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List


def run(cmd: List[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def git_root() -> Path:
    p = run(["git", "rev-parse", "--show-toplevel"])
    if p.returncode != 0:
        raise RuntimeError("Не удалось определить git root. Вы внутри git-репозитория?")
    return Path(p.stdout.strip())


def build_diff_cmd(args: argparse.Namespace) -> List[str]:
    base = ["git", "diff", "--no-color"]
    if args.unified is not None:
        base += [f"--unified={args.unified}"]

    if args.staged:
        base += ["--cached"]

    if args.ref:
        # Для PR-подобного сравнения чаще удобен triple-dot (через merge-base).
        # Но если вам нужно строгое сравнение ref..HEAD — поменяйте на \"..\".
        base += [f"{args.ref}...HEAD"]
    elif args.range:
        base += [args.range]

    return base


def pick_editor() -> List[str]:
    editor = os.environ.get("EDITOR", "").strip()
    if editor:
        return shlex.split(editor)
    # фоллбеки — лучше иметь хотя бы один из них
    for cand in ("micro", "nano", "vi"):
        if shutil_which(cand):
            return [cand]
    return ["vi"]


def shutil_which(name: str) -> str | None:
    # минимальная реализация which без shutil (чтобы быть самодостаточными)
    paths = os.environ.get("PATH", "").split(os.pathsep)
    exts = [""]
    if os.name == "nt":
        exts = os.environ.get("PATHEXT", "").split(os.pathsep)
    for p in paths:
        for ext in exts:
            candidate = Path(p) / f"{name}{ext}"
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Аннотационное ревью git diff через $EDITOR")
    ap.add_argument("--ref", help="Сравнить с ref (используется <ref>...HEAD)")
    ap.add_argument("--range", help="Явный range для git diff (например, HEAD~3..HEAD)")
    ap.add_argument("--staged", action="store_true", help="Использовать --cached (staged changes)")
    ap.add_argument("--unified", type=int, default=3, help="Контекст diff (по умолчанию 3)")
    ap.add_argument("--keep", action="store_true", help="Не удалять временный файл")
    ap.add_argument("--test", action="store_true", help="Проверка окружения/доступа к git")
    args = ap.parse_args()

    try:
        root = git_root()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.test:
        cmd = build_diff_cmd(args)
        p = run(cmd, cwd=str(root))
        if p.returncode != 0:
            print("ERROR: git diff не выполнился:", file=sys.stderr)
            print(p.stderr, file=sys.stderr)
            return 3
        print("OK")
        return 0

    cmd = build_diff_cmd(args)
    p = run(cmd, cwd=str(root))
    if p.returncode != 0:
        print("ERROR: git diff не выполнился:", file=sys.stderr)
        print(p.stderr, file=sys.stderr)
        return 3

    diff_text = p.stdout
    if not diff_text.strip():
        # нечего ревьюить
        return 0

    # Пишем во временный файл
    fd, tmp_path = tempfile.mkstemp(prefix="git-review-", suffix=".diff", text=True)
    os.close(fd)
    tmp = Path(tmp_path)
    tmp.write_text(diff_text, encoding="utf-8")

    original = diff_text.splitlines(keepends=True)

    editor_cmd = pick_editor()
    try:
        # editor может быть чем-то вроде: "code --wait"
        subprocess.run(editor_cmd + [str(tmp)], cwd=str(root))
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f"ERROR: не удалось запустить редактор ({editor_cmd}): {e}", file=sys.stderr)
        return 4

    updated_text = tmp.read_text(encoding="utf-8")
    updated = updated_text.splitlines(keepends=True)

    if not args.keep:
        try:
            tmp.unlink(missing_ok=True)  # py3.8+ поддерживает missing_ok
        except TypeError:
            if tmp.exists():
                tmp.unlink()

    if updated == original:
        # Пользователь ничего не поменял — считаем ревью завершённым
        return 0

    # Печатаем unified diff «аннотаций»
    ud = difflib.unified_diff(
        original,
        updated,
        fromfile="a/review.diff",
        tofile="b/review.diff",
        lineterm="",
    )
    sys.stdout.write("\n".join(ud))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
