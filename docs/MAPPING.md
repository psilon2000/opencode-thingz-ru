# Соответствие cc-thingz → OpenCode

Этот репозиторий переносит идеи cc-thingz в реалии OpenCode.

## Что переносится почти 1:1

- **Skills**: структурированные промпты для брейншторма, ревью, мышления, workflow.
- **Командные обёртки**: чтобы запускать workflow одной командой.
- **Скрипты аннотаций**: редактирование diff/плана в $EDITOR с возвратом unified diff.
- **Custom rules**: идея project/user overrides переносится, но с OpenCode-путями (`.opencode/*.md`, `~/.config/opencode/*.md`) вместо `.claude/*` и `$CLAUDE_PLUGIN_DATA/*`.

## Что переносится частично

- **Hooks** Claude Code (`UserPromptSubmit`, `PreToolUse ExitPlanMode`)  
  В OpenCode это логичнее делать через:
  - Rules (проще, переносимо),
  - или Plugins (если нужен хук на каждый ввод/интерактив TUI).

В этом наборе `skill-eval` реализован как **rule** (меньше зависимости от API плагинов).

## Что не переносится «как есть»

- Полная интеграция «перехват выхода из plan-mode → открыть редактор → отменить tool call» —
  в OpenCode зависит от конкретных событий TUI и может отличаться.
  Здесь дан минимальный скрипт `plan-annotate.py` и командная схема.

## Идеи для доработки (в вашем приватном форке)

- Сделать plugin для `skill-eval`, который добавляет напоминание в каждый prompt (TUI hook).
- Завести custom tool для запуска `plan-annotate.py` и `git-review.py` с обработкой интерактива.
- Уточнить правила генерации release notes под вашу конвенцию (Conventional Commits / PR labels).
