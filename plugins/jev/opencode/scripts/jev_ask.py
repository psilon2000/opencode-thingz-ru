#!/usr/bin/env python3
"""Массовые типизированные решения через Jev (TypeSafe System One).

Элементы читаются из файла или stdin, каждый получает один и тот же вопрос; Jev отвечает
вероятностями. На stdout печатается короткая сводка, полные результаты (без текстов) — в --out.
Только стандартная библиотека.

Форматы входа:
  JSONL: {"id": ..., "text": ...} (поля меняются --id-field / --text-field); JSON-массив таких объектов;
  --lines: каждая непустая строка — элемент, id — номер строки.

Ключ: TYPESAFE_API_KEY или ~/.config/typesafe/api_key. Журнал запусков без текстов:
$JEV_ASK_STATE_DIR/log.jsonl (по умолчанию ~/.local/state/jev-ask).

Примеры:
  jev_ask.py --items tasks.jsonl --type noul --question "Does the task contain acceptance criteria?"
  grep ERROR app.log | jev_ask.py --lines --type choice --question "Root cause category?" \\
      --criteria '{"db": "database", "network": "network", "app": "application bug", "noise": "not a problem"}' \\
      --filter secrets --out result.jsonl
  jev_ask.py --test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-1.13.0"  # закреплённая версия: у алиаса jev-latest поведение может смениться
KEY_FILE = Path.home() / ".config/typesafe/api_key"
STATE_DIR = Path(os.environ.get("JEV_ASK_STATE_DIR") or Path.home() / ".local/state/jev-ask")

SECRETS = [
    r"glpat-[\w-]{20,}", r"gh[pousr]_[A-Za-z0-9]{30,}", r"xox[abprs]-[\w-]{10,}", r"AKIA[0-9A-Z]{16}",
    r"sk-(ant-)?[A-Za-z0-9_-]{20,}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}", r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}",
    r"(?i)\b(password|passwd|pwd|пароль)\s*[:=]\s*['\"]?(?=[^\s'\"]*[\d!@#$%^&*])[^\s'\"]{6,}",
    r"(?i)\b(password|pwd)=[^;\s]{3,};", r"\b[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s@/]{3,}@",
]
PERSONAL = [
    r"(?<![\d+])(?:\+7|8)[\s\-(]*\d{3}[\s\-)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}(?!\d)",  # телефон РФ
    r"(?<!\d)\d{12}(?!\d)",  # ИНН физлица или ИП
    r"(?<!\d)\d{3}-\d{3}-\d{3}[ -]\d{2}(?!\d)",  # СНИЛС
    r"(?i)паспорт\D{0,20}\d{2}\s?\d{2}\s?\d{6}",
    r"(?i)(зарплат|зп\b|оклад|преми[яию]|увол[иь]|оффер|компенсаци|больнич|заболе|болеет|декрет|на руки|ндфл"
    r"|диагноз|медицинск)",
    r"(?i)(?<![\w.])\d{2,3}\s?(к|тыс)\b",
]
FILTERS = {"strict": SECRETS + PERSONAL, "secrets": SECRETS, "off": []}


def luhn_card(text: str) -> bool:
    for match in re.finditer(r"(?<![\d-])(\d{16,19}|\d{4}([ -])\d{4}\2\d{4}\2\d{4})(?![\d-])", text):
        digits = re.sub(r"\D", "", match.group(1))
        total = 0
        for index, char in enumerate(reversed(digits)):
            number = int(char) * (2 if index % 2 else 1)
            total += number - 9 if number > 9 else number
        if digits[0] in "23456" and total % 10 == 0:
            return True
    return False


def blocked(text: str, mode: str) -> bool:
    if mode == "off":
        return False
    return luhn_card(text) or any(re.search(pattern, text) for pattern in FILTERS[mode])


def read_items(source: str, lines: bool, id_field: str, text_field: str) -> list[dict]:
    raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    if lines:
        return [{"id": number, "text": line.strip()} for number, line in enumerate(raw.splitlines(), 1) if line.strip()]
    stripped = raw.lstrip()
    records = json.loads(stripped) if stripped.startswith("[") else [json.loads(line) for line in raw.splitlines() if line.strip()]
    items = []
    for number, record in enumerate(records, 1):
        if isinstance(record, str):
            items.append({"id": number, "text": record})
        else:
            items.append({"id": record.get(id_field, number), "text": str(record.get(text_field) or "")})
    return [item for item in items if item["text"].strip()]


def parse_criteria(value: str | None):
    if not value:
        return None
    return json.loads(Path(value[1:]).read_text(encoding="utf-8") if value.startswith("@") else value)


def build_question(kind: str, question: str, criteria, text: str) -> dict:
    spec = {"type": kind, "instructions": f"{question}\nItem: «{text}»"}
    if criteria is not None:
        spec["criteria"] = criteria
    return spec


def make_batches(items: list[dict], max_chars: int, batch_chars: int) -> list[list[dict]]:
    batches, current, size = [], [], 0
    for item in items:
        length = min(len(item["text"]), max_chars) + 300
        if current and size + length > batch_chars:
            batches.append(current)
            current, size = [], 0
        current.append(item)
        size += length
    if current:
        batches.append(current)
    return batches


def api_key() -> str | None:
    key = os.environ.get("TYPESAFE_API_KEY")
    if key:
        return key.strip()
    try:
        return KEY_FILE.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def ask(key: str, model: str, state, questions: dict, timeout: float) -> dict:
    body = json.dumps({"model": model, "state": state, "questions": questions}).encode("utf-8")
    request = urllib.request.Request(URL, data=body, method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as error:
        return {"error": f"HTTP {error.code}: {error.read()[:200].decode('utf-8', 'replace')}"}
    except (OSError, ValueError) as error:
        return {"error": str(error)[:200]}
    return {"answers": payload.get("answers") or {}, "model": payload.get("model"),
            "input_tokens": (payload.get("usage") or {}).get("input_tokens") or 0}


def interpret(kind: str, answer: dict, threshold: float) -> dict:
    """Ответ Jev -> {"label", "p", ...}. Для choice ниже порога метка «uncertain»."""
    if not answer:
        return {"label": "error"}
    if kind == "noul":
        p = round(float(answer.get("noul") or 0.0), 3)
        return {"label": "yes" if p >= threshold else "no", "p": p}
    if kind == "choice":
        probabilities = {name: round(float(value), 3) for name, value in (answer.get("probabilities") or {}).items()}
        top = answer.get("choice") or (max(probabilities, key=probabilities.get) if probabilities else None)
        p = probabilities.get(top, float(answer.get("confidence") or 0.0))
        return {"label": top if p >= threshold else "uncertain", "choice": top, "p": round(p, 3), "probabilities": probabilities}
    score = round(float(answer.get("score") or 0.0), 3)
    return {"label": str(round(score)), "score": score, "p": round(float(answer.get("confidence") or 0.0), 3),
            "probabilities": answer.get("probabilities") or {}}


def summarize(kind: str, items: list[dict], results: dict, skipped: list[dict], meta: dict, args) -> str:
    def excerpt(item):
        flat = " ".join(item["text"].split())
        return flat if len(flat) <= 140 else flat[:139] + "…"

    done = [item for item in items if item["id"] in results and results[item["id"]]["label"] != "error"]
    errors = [item for item in items if item["id"] not in results or results[item["id"]]["label"] == "error"]
    counts: dict[str, int] = {}
    for item in done:
        counts[results[item["id"]]["label"]] = counts.get(results[item["id"]]["label"], 0) + 1
    lines = [
        f"Jev {meta.get('model') or args.model}: {kind}, элементов {len(items) + len(skipped)}, оценено {len(done)}, "
        f"пропущено фильтром ({args.filter}) {len(skipped)}, ошибок {len(errors)}; пачек {meta['batches']}, "
        f"входных токенов {meta['input_tokens']}, {meta['ms'] / 1000:.1f} с.",
        "Итог (порог " + str(args.threshold) + "): " + ", ".join(f"{label} — {count}" for label, count in sorted(counts.items(), key=lambda pair: -pair[1])),
    ]
    if meta.get("errors"):
        lines.append("Ошибки API: " + "; ".join(meta["errors"][:3]))
    for label in sorted(counts, key=lambda name: -counts[name]):
        group = sorted((item for item in done if results[item["id"]]["label"] == label),
                       key=lambda item: -results[item["id"]]["p"])[: args.show]
        lines.append(f"Примеры «{label}»:")
        lines += [f"  {item['id']} ({results[item['id']]['p']:.2f}) «{excerpt(item)}»" for item in group]
    if args.borderline:
        border = sorted(done, key=lambda item: abs(results[item["id"]]["p"] - args.threshold))[: args.borderline]
        lines.append(f"Ближе всего к порогу (проверь вручную):")
        lines += [f"  {item['id']} {results[item['id']]['label']} ({results[item['id']]['p']:.2f}) «{excerpt(item)}»" for item in border]
    if skipped:
        lines.append("Пропущены фильтром (id): " + ", ".join(str(item["id"]) for item in skipped[:30]) + (" …" if len(skipped) > 30 else ""))
    if args.out:
        lines.append(f"Полные результаты: {args.out}")
    return "\n".join(lines)


def run(args) -> int:
    criteria = parse_criteria(args.criteria)
    if args.type in ("choice", "score") and not criteria:
        sys.exit("jev_ask: для choice и score нужны --criteria")
    items = read_items(args.items, args.lines, args.id_field, args.text_field)
    if args.limit:
        items = items[: args.limit]
    skipped = [item for item in items if blocked(item["text"], args.filter)]
    items = [item for item in items if not blocked(item["text"], args.filter)]
    batches = make_batches(items, args.max_chars, args.batch_chars)
    if args.dry_run:
        print(f"Сухой прогон: элементов {len(items) + len(skipped)}, к отправке {len(items)}, "
              f"пропущено фильтром ({args.filter}) {len(skipped)}, пачек {len(batches)}, "
              f"символов к отправке ≈ {sum(min(len(item['text']), args.max_chars) for item in items)}.")
        return 0
    key = api_key()
    if not key:
        sys.exit("jev_ask: нет ключа — задайте TYPESAFE_API_KEY или запишите его в ~/.config/typesafe/api_key")

    results: dict = {}
    errors: list[str] = []
    tokens = 0
    model = None

    def one(batch):
        questions = {f"q{index}": build_question(args.type, args.question, criteria, item["text"][: args.max_chars])
                     for index, item in enumerate(batch)}
        return batch, ask(key, args.model, args.state or "", questions, args.timeout)

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for batch, response in pool.map(one, batches):
            if "error" in response:
                errors.append(response["error"])
                continue
            tokens += response["input_tokens"]
            model = response["model"]
            for index, item in enumerate(batch):
                results[item["id"]] = interpret(args.type, response["answers"].get(f"q{index}") or {}, args.threshold)
    meta = {"batches": len(batches), "input_tokens": tokens, "ms": int((time.monotonic() - started) * 1000),
            "errors": errors, "model": model}

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps({"id": item["id"], **results.get(item["id"], {"label": "error"})}, ensure_ascii=False) + "\n")
            for item in skipped:
                handle.write(json.dumps({"id": item["id"], "label": "skipped", "reason": f"filter:{args.filter}"}, ensure_ascii=False) + "\n")
    print(summarize(args.type, items, results, skipped, meta, args))
    try:
        STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (STATE_DIR / "log.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "type": args.type, "model": model,
                "question_hash": hashlib.sha256(args.question.encode("utf-8")).hexdigest()[:12],
                "items": len(items) + len(skipped), "sent": len(items), "skipped": len(skipped), "filter": args.filter,
                "errors": len(errors), "input_tokens": tokens, "ms": meta["ms"],
            }) + "\n")
    except OSError:
        pass
    return 1 if errors and not results else 0


def self_test() -> int:
    assert blocked("Карта 4111 1111 1111 1111", "secrets")
    assert blocked("token glpat-abcdefghijklmnopqrstuv", "secrets")
    assert not blocked("Позвони +7 912 345-67-89", "secrets")
    assert blocked("Позвони +7 912 345-67-89", "strict")
    assert blocked("Хочет уволиться", "strict")
    assert not blocked("Карта 4111 1111 1111 1111", "off")
    assert not blocked("ERROR connection refused to db-test-01:5432", "strict")
    assert interpret("noul", {"noul": 0.8}, 0.5) == {"label": "yes", "p": 0.8}
    assert interpret("choice", {"choice": "db", "probabilities": {"db": 0.4, "app": 0.35, "noise": 0.25}}, 0.5)["label"] == "uncertain"
    assert interpret("choice", {"choice": "db", "probabilities": {"db": 0.9, "app": 0.1}}, 0.5)["label"] == "db"
    assert interpret("score", {"score": 2.4, "confidence": 0.7}, 0.5)["label"] == "2"
    assert interpret("noul", {}, 0.5) == {"label": "error"}
    items = [{"id": n, "text": "x" * 1000} for n in range(10)]
    assert [len(batch) for batch in make_batches(items, 3000, 5000)] == [3, 3, 3, 1]
    spec = build_question("choice", "Category?", {"a": "A"}, "text")
    assert spec["criteria"] == {"a": "A"} and spec["instructions"].endswith("Item: «text»")
    print("jev_ask self-test: ok")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Массовые типизированные решения через Jev")
    parser.add_argument("--items", default="-", help="файл JSONL / JSON-массив или «-» для stdin")
    parser.add_argument("--lines", action="store_true", help="каждая непустая строка — элемент")
    parser.add_argument("--id-field", default="id")
    parser.add_argument("--text-field", default="text")
    parser.add_argument("--type", choices=["noul", "choice", "score"], default="noul")
    parser.add_argument("--question", help="вопрос к каждому элементу (лучше по-английски, тексты могут быть на любом языке)")
    parser.add_argument("--criteria", help="JSON или @файл: noul — {true, false}; choice — {метка: описание}; score — [уровни]")
    parser.add_argument("--state", help="общий контекст для всех элементов")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--filter", choices=list(FILTERS), default="strict",
                        help="strict — секреты и персональные данные; secrets — только секреты и карты; off — без фильтра")
    parser.add_argument("--out", help="JSONL с результатами без текстов")
    parser.add_argument("--show", type=int, default=3, help="примеров на метку в сводке")
    parser.add_argument("--borderline", type=int, default=5, help="элементов ближе всего к порогу")
    parser.add_argument("--limit", type=int, help="взять только первые N элементов")
    parser.add_argument("--max-chars", type=int, default=3000)
    parser.add_argument("--batch-chars", type=int, default=50000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dry-run", action="store_true", help="только подсчёт: что уйдёт и что отфильтровано")
    parser.add_argument("--test", action="store_true", help="самопроверка без сети")
    args = parser.parse_args()
    if args.test:
        return self_test()
    if not args.question:
        parser.error("нужен --question")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
