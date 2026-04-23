# opencode-thingz (RU)

Набор «плагинов» (в виде переносимых конфигов) для **OpenCode**: навыки (skills), команды (commands), пользовательские инструменты (custom tools) и вспомогательные скрипты.

Этот репозиторий **вдохновлён** идеей *cc-thingz* (Umputun): собирать прикладные рабочие приёмы в независимые модули и подключать их по необходимости.

## Что внутри

Все модули лежат в `plugins/<имя>/opencode/…`. Установка — это копирование файлов модуля в:

- **глобальную конфигурацию** OpenCode: `~/.config/opencode/`
- или **конфигурацию проекта**: `<проект>/.opencode/`

Модули:

- `brainstorm` — структурированный брейншторм: идея → варианты → дизайн → следующий шаг.
- `review` — ревью PR/issue (через `gh`), стиль коротких тех-комментариев, и «аннотационное ревью» диффа.
- `planning` — генерация плана внедрения в `docs/plans/…`, авто-проверка качества плана, и скрипт аннотаций плана.
- `release-tools` — «черновой» релиз-процесс: следующий semver, список изменений с последнего тега, заметки релиза и helper scripts.
- `thinking-tools` — диалектика (за/против), «5 почему» и optional second opinion через `codex`.
- `skill-eval` — правило «сначала проверь доступные навыки».
- `workflow` — рабочие «хелперы»: сохранить знание в `AGENTS.md`, разобрать непонимание, перезапуск подхода, копирование в буфер.

## Быстрый старт

### Установить все модули в текущий проект

```bash
./install.sh --project .
```

### Установить выборочно в глобальную конфигурацию

```bash
./install.sh --global brainstorm review workflow
```

## Требования / ожидания

- Для модуля `review` (PR/issue ревью) нужен **GitHub CLI** (`gh`) и авторизация.
- Скрипты аннотаций (`plan-annotate.py`, `git-review.py`) рассчитаны на запуск в вашем терминале и открытие файла в `$EDITOR`.

## Custom Rules

Для модулей `planning` и `brainstorm` поддерживаются дополнительные правила поверх встроенных skill/command-инструкций.

- проектный уровень: `.opencode/planning-rules.md`, `.opencode/brainstorm-rules.md`
- глобальный уровень: `~/.config/opencode/planning-rules.md`, `~/.config/opencode/brainstorm-rules.md`

Приоритет у проектного файла. Если проектный файл пустой или отсутствует, берётся глобальный.

Связанные скрипты:

- `.opencode/scripts/planning-resolve-rules.sh`
- `.opencode/scripts/brainstorm-resolve-rules.sh`

## Проверки

В репозитории есть базовый CI workflow и локальные проверки для текущего среза синхронизации:

- shell tests: `bash tests/test-planning-resolve-rules.sh` и `bash tests/test-brainstorm-resolve-rules.sh`
- python smoke tests: `python3 plugins/planning/opencode/scripts/plan-annotate.py --test` и `python3 plugins/review/opencode/scripts/git-review.py --test`
- GitHub Actions workflow: `.github/workflows/ci.yml`

## Как пользоваться

1) Скопируйте модуль (через `install.sh`).
2) В OpenCode используйте:
- либо **команды** (файлы в `.opencode/commands/…`, вызываются как `/…` в интерфейсе OpenCode),
- либо просите агента явно применить соответствующий **skill**.

Подсказка: если вы включили модуль `skill-eval`, агент будет стараться **сначала** подобрать и активировать подходящий skill.

## Где хранится «память проекта»

Модуль `workflow` пишет выбранные вами «правила и знания проекта» в файл `AGENTS.md` в корне репозитория (если файла нет — создаст).

## Лицензия

Эта заготовка рассчитана на приватное использование. Если нужно — добавьте лицензию, принятую у вас в компании/проекте.
