#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
plan-annotate.py — открыть markdown-план в $EDITOR и вывести unified diff изменений.

Использование:
  python3 .opencode/scripts/plan-annotate.py docs/plans/2026-03-02-foo.md

Поведение:
- Если пользователь закрыл редактор без изменений → ничего не печатаем.
- Если изменил → печатаем unified diff (его удобно вставить в чат для агента).

Это минимальная версия под OpenCode. При желании можно добавить интеграции
с tmux/kitty/wezterm и режимы «перехвата» как в Claude Code.
"""

from __future__ import annotations

import argparse
import difflib
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List


def which(name: str) -> str | None:
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


def pick_editor() -> List[str]:
    editor = os.environ.get("EDITOR", "").strip()
    if editor:
        return shlex.split(editor)
    for cand in ("micro", "nano", "vi"):
        if which(cand):
            return [cand]
    return ["vi"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Аннотирование плана через $EDITOR")
    ap.add_argument("file", nargs="?", help="Путь к плану (markdown)")
    ap.add_argument("--test", action="store_true", help="Проверка доступности редактора")
    args = ap.parse_args()

    if args.test:
        cmd = pick_editor()
        print("OK editor:", " ".join(cmd))
        return 0

    if not args.file:
        print("ERROR: не указан файл плана", file=sys.stderr)
        return 2

    f = Path(args.file)
    if not f.exists():
        print(f"ERROR: файл не найден: {f}", file=sys.stderr)
        return 3

    original_text = f.read_text(encoding="utf-8")
    original = original_text.splitlines(keepends=True)

    editor_cmd = pick_editor()
    try:
        subprocess.run(editor_cmd + [str(f)])
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f"ERROR: не удалось запустить редактор ({editor_cmd}): {e}", file=sys.stderr)
        return 4

    updated_text = f.read_text(encoding="utf-8")
    updated = updated_text.splitlines(keepends=True)

    if updated == original:
        return 0

    ud = difflib.unified_diff(
        original,
        updated,
        fromfile=f"a/{f}",
        tofile=f"b/{f}",
        lineterm="",
    )
    sys.stdout.write("\n".join(ud))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
