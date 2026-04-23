# Использование в OpenCode

Этот набор предполагает, что OpenCode читает конфиги из:

- `<repo>/.opencode/` (локально для проекта)
- `~/.config/opencode/` (глобально)

## Варианты установки

### В проект

1) Скопируйте содержимое `dist/.opencode/` в `<ваш-проект>/.opencode/`
2) Или выполните из корня этого репозитория:

```bash
./install.sh --project <ваш-проект> brainstorm review planning
```

### Глобально

```bash
./install.sh --global workflow skill-eval
```

## Как запускать

- Команды лежат в `.opencode/commands/*.md` и обычно вызываются как `/имя-команды` в интерфейсе OpenCode.
- Skills лежат в `.opencode/skills/*/SKILL.md`. Если агент не активирует skill автоматически, попросите явно:
  - «активируй skill `review-pr` и сделай ревью PR 123»
  - или используйте соответствующую команду `/review-pr 123`.

## Скрипты

Скрипты лежат в `.opencode/scripts/` и рассчитаны на запуск пользователем в терминале:

- `python3 .opencode/scripts/plan-annotate.py <file>`
- `python3 .opencode/scripts/git-review.py [--ref <ref>]`
- `bash .opencode/scripts/planning-resolve-rules.sh planning-rules.md`
- `bash .opencode/scripts/brainstorm-resolve-rules.sh brainstorm-rules.md`
- `bash .opencode/scripts/detect-platform.sh`
- `bash .opencode/scripts/calc-version.sh hotfix`
- `bash .opencode/scripts/get-notes.sh github`

Если хотите запускать их прямо из OpenCode через `bash` — убедитесь, что ваш OpenCode/терминал корректно работает с интерактивными программами.

## Custom Rules

Для `planning` и `brainstorm` можно завести дополнительные правила:

- проектные: `.opencode/planning-rules.md`, `.opencode/brainstorm-rules.md`
- глобальные: `~/.config/opencode/planning-rules.md`, `~/.config/opencode/brainstorm-rules.md`

Сначала читается проектный файл, потом глобальный. Это позволяет хранить общие предпочтения в глобальной конфигурации, а project-specific ограничения держать рядом с кодом.
