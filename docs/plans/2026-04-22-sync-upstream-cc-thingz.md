# План: синхронизация с upstream `umputun/cc-thingz`

## Цель / Не-цель

**Цель**

- Максимально синхронизировать `opencode-thingz-ru` с актуальным `umputun/cc-thingz`, не ограничиваясь `planning`, а покрыв все локальные плагины.
- Перенести полезные upstream-изменения по структуре, сценариям, скриптам, тестам и CI.
- Сохранить локальную русификацию и OpenCode-адаптацию там, где это не мешает сближению с upstream.
- После синхронизации сохранить рабочие сценарии установки через `install.sh` и через копирование `dist/.opencode/`.

**Не-цель**

- Не делать слепой 1:1 перенос Claude-специфичных хуков и сценариев без проверки, что они применимы в OpenCode.
- Не переписывать архитектуру репозитория сверх того, что требуется для синхронизации с upstream.
- Не выпускать релиз и не менять пользовательские процессы вне области портирования без отдельного решения.

## Критерии готово

- Все локальные плагины сравнились с `umputun/cc-thingz@master`, и по каждому значимому расхождению зафиксирован статус `port`, `adapt` или `reject` с причиной.
- Repo-level инфраструктура качества из upstream перенесена, и локальный репозиторий получил рабочие `tests/**` и `.github/workflows/ci.yml`.
- Для каждого Claude-only, hook-only или terminal-specific элемента принято и записано решение: переносим как есть, адаптируем под OpenCode или сознательно не переносим.
- Источником правды остаются `plugins/**`; publishable-слой `dist/.opencode/**` обновлён на их основе и не расходится с ними по целевым файлам.
- Обновлённые плагины устанавливаются через `./install.sh --project <tmp-dir>` и через копирование `dist/.opencode/` без нарушения ожидаемой структуры `.opencode/`.
- Локальные проверки и CI-проверки, добавленные в рамках sync, проходят на ветке с изменениями.
- По итогам работ есть короткий отчёт: что перенесено, что адаптировано, что отклонено и почему.

## Предпосылки и ограничения

- Локальный репозиторий пока сильно отстаёт от upstream: в локальной истории всего 2 коммита, при этом upstream активно менялся в марте-апреле 2026.
- Набор плагинов локально и в upstream совпадает по верхнему уровню: `brainstorm`, `planning`, `release-tools`, `review`, `skill-eval`, `thinking-tools`, `workflow`.
- Локально уже есть собственная адаптация: русские тексты, OpenCode layout (`plugins/*/opencode/**`, `dist/.opencode/**`) и переименованные slug'и в kebab-case.
- Upstream уже добавил изменения, которые выглядят полезными для переноса: `tests/**`, `.github/workflows/ci.yml`, custom rules injection для `planning` и `brainstorm`, развитие `planning`, новые/переименованные skills и исправления shell/python-скриптов.
- В локальном репозитории сейчас нет `tests/` и нет CI, значит их перенос нужно считать отдельной обязательной частью работы.
- `dist/.opencode/**` является publishable-слоем поверх исходников в `plugins/**`; после каждого портирования нужно держать эти деревья синхронными.
- `plugins/**` считаются source of truth; любые содержательные правки сначала вносятся туда, и только потом зеркалируются в `dist/.opencode/**`.
- При конфликте приоритет такой: upstream-поведение и полезная механика важнее, но локальная русификация и OpenCode-специфика сохраняются, если не ломают синхронизацию.

## Подход (кратко)

- Идти не по файлам, а по фазам: сначала зафиксировать baseline и матрицу различий, затем перенести repo-level инфраструктуру, потом синхронизировать плагины по приоритету, после этого обновить `dist` и документацию, и только в конце закрыть полную проверку.
- Для каждого upstream-изменения явно присваивать статус: `port as-is`, `adapt`, `reject with reason`.
- Начать с самых рискованных и самых ценных зон: `planning`, `brainstorm`, `tests/CI`.
- Все Claude-only и hook-only куски переносить только после проверки, что у них есть рабочий эквивалент в OpenCode; иначе оставлять в списке осознанно не перенесённых элементов.

## Задачи

Фаза 1. Baseline и правила синхронизации

- [x] Зафиксировать локальный baseline: записать текущий `HEAD`, дату/sha upstream `umputun/cc-thingz@master` и список repo-level файлов и плагинов, которые участвуют в сравнении.
- [x] Составить матрицу различий по repo-level файлам и каждому плагину со статусами `port`, `adapt`, `reject`.
- [x] В этой же матрице отдельно отметить все Claude-only, hook-only и terminal-specific элементы.
- [x] Зафиксировать правило sync в явном виде: что переносится как есть, что адаптируется под OpenCode/RU, что не переносится.
- [x] Зафиксировать рабочее правило публикации: source of truth находится в `plugins/**`, а `dist/.opencode/**` обновляется только после изменений в исходниках.

Фаза 2. Repo-level инфраструктура

- [x] Перенести релевантные для текущего среза `tests/**`: shell tests для `planning` и `brainstorm` custom rules. Тесты для `planning:exec` не переносить, потому что сам `exec` имеет статус `reject` в текущем sync-срезе.
- [x] Перенести из upstream `.github/workflows/ci.yml` и минимальные repo-level изменения, без которых CI или локальные проверки не запускаются.
- [x] Прогнать локально доступные тестовые и quality-скрипты и исправить базовые несовместимости, мешающие перейти к модульному sync.
- [x] Зафиксировать минимальный набор команд, который должен проходить локально и в CI после завершения sync.
- [x] Для локального quality-прогона установлены `shellcheck` и `PyYAML`; CI-минимум теперь подтверждён не только workflow-конфигом, но и локальным прогоном.

Фаза 3. `planning`

- [x] Сравнить локальный `planning` с upstream и выделить отдельно команды, skills, scripts, references и hooks.
- [x] Перенести safe changes в `planning`: исправления path resolution, custom rules injection, улучшения сценария создания/ревью плана, не завязанные на Claude-only runtime.
- [x] Для `planning`-элементов `exec`, hooks и review-hook принять отдельное решение `adapt` или `reject` с коротким обоснованием.
- [x] Адаптация Claude-only частей для `planning` не требуется в текущем срезе: для `exec` и hooks принято решение `reject`, зафиксированное в матрице.
- [x] Обновить `dist/.opencode/**` для `planning` на основе `plugins/planning/**`.
- [x] Прогнать script-level и smoke-проверки для `planning`.

Фаза 4. `brainstorm`

- [x] Сравнить локальный `brainstorm` с upstream и выделить отдельно skills, scripts и references.
- [x] Перенести в `brainstorm` safe changes: `resolve-rules.sh`, reference-доки и улучшения содержимого skill, совместимые с OpenCode.
- [x] Для отличий в именах, layout и текстах зафиксировать, что оставляем локально, а что сближаем с upstream.
- [x] Обновить `dist/.opencode/**` для `brainstorm` на основе `plugins/brainstorm/**`.
- [x] Прогнать script-level и smoke-проверки для `brainstorm`.

Фаза 5. Остальные плагины высокого и среднего приоритета

- [x] Сравнить и синхронизировать `review`: отдельно перенести safe changes в skills и `git-review.py`, а terminal-specific части пометить решением `adapt` или `reject`.
- [x] Сравнить и синхронизировать `release-tools`: перенести shell-исправления, обновления логики release notes и связанные scripts/docs, если они не завязаны на Claude-only среду.
- [x] Сравнить и синхронизировать `skill-eval`: решить судьбу upstream hooks и перенести только совместимые с OpenCode части.
- [x] Сравнить и синхронизировать `thinking-tools`: перенести новые и переименованные skills, если они полезны и не конфликтуют с локальной терминологией.
- [x] Сравнить и синхронизировать `workflow`: перенести полезные изменения в skills и tools без поломки текущих OpenCode-сценариев.
- [x] После каждого из этих плагинов обновлять соответствующие файлы в `dist/.opencode/**` и сразу отмечать статус в матрице различий.

Фаза 6. Документация и публикация

- [x] Обновить `README.md` под новую механику sync, quality checks и правила обновления плагинов.
- [x] Обновить `docs/MAPPING.md` и `docs/USAGE.md` с учётом реально перенесённых upstream-возможностей и осознанно не перенесённых частей.
- [x] Обновить `plugins/*/README.md` там, где changed behavior, новые scripts или новые ограничения требуют пользовательских инструкций.
- [x] Выполнить финальную синхронизацию `dist/.opencode/**` из `plugins/**` и проверить, что publishable-слой соответствует источникам.

Фаза 7. Финальная проверка и закрытие

- [x] Прогнать весь набор локальных тестов и quality-проверок, перенесённых из upstream.
- [x] Проверить, что GitHub Actions workflow логически соответствует локальным проверкам и должен проходить на ветке с sync.
- [x] Выполнить smoke-установку в временный проект через `./install.sh --project <tmp-dir>` и отдельно через копирование `dist/.opencode/`.
- [x] Проверить наличие и читаемость ключевых команд, skills и scripts после установки.
- [ ] Подготовить короткий итоговый отчёт: что перенесено, что адаптировано, что отклонено и почему.
- [x] Локально подтверждены frontmatter/YAML check, `shellcheck`, shell tests, python smoke tests и `release-tools` smoke.

## Затронутые файлы/модули (если известно)

- Repo-level: `README.md`, `docs/MAPPING.md`, `docs/USAGE.md`, `install.sh`, `.github/workflows/ci.yml`, `tests/**`, `docs/plans/**`.
- `planning`: `plugins/planning/**`, `dist/.opencode/commands/plan-make.md`, `dist/.opencode/skills/plan-review/SKILL.md`, `dist/.opencode/scripts/plan-annotate.py`.
- Вероятные новые кандидаты из upstream для адаптации в `planning`: `plugins/planning/scripts/resolve-rules.sh`, `plugins/planning/scripts/plan-review-hook.py`, `plugins/planning/references/**`, `plugins/planning/skills/exec/**`.
- `brainstorm`: `plugins/brainstorm/**`, `dist/.opencode/commands/brainstorm.md`, `dist/.opencode/skills/brainstorm-do/SKILL.md`.
- Вероятные новые кандидаты из upstream для адаптации в `brainstorm`: `plugins/brainstorm/scripts/resolve-rules.sh`, `plugins/brainstorm/references/**`, обновлённый skill layout.
- `review`: `plugins/review/**`, `dist/.opencode/commands/git-review.md`, `dist/.opencode/commands/review-pr.md`, `dist/.opencode/commands/writing-style.md`, `dist/.opencode/scripts/git-review.py`, `dist/.opencode/skills/review-*/**`.
- `release-tools`: `plugins/release-tools/**`, `dist/.opencode/commands/release-*.md`, `dist/.opencode/skills/release-*/**`.
- `skill-eval`: `plugins/skill-eval/**`, `dist/.opencode/rules/00-skill-eval.md`.
- `thinking-tools`: `plugins/thinking-tools/**`, `dist/.opencode/commands/dialectic.md`, `dist/.opencode/commands/root-cause.md`, `dist/.opencode/skills/thinking-*/**`.
- `workflow`: `plugins/workflow/**`, `dist/.opencode/commands/wf-*.md`, `dist/.opencode/skills/workflow-*/**`, `dist/.opencode/tools/clipboard.ts`.

## Тест-план

**Unit / script-level**

- Перенести и запустить upstream shell-тесты для `planning` и `brainstorm` rule resolution.
- Перенести и запустить тесты для `planning` exec/vcs-скриптов, если будет принято решение переносить `exec`-ветку.
- Проверить Python-скрипты (`plan-annotate.py`, `git-review.py`) хотя бы на уровне запуска `--help` и корректного импорта зависимостей.
- Проверить YAML/frontmatter и shellcheck-подобные проблемы для markdown/shell-файлов, если это покрывается CI из upstream.
- Зафиксировать конкретные команды локальной проверки и использовать их как acceptance-набор для CI.

**Integration**

- Выполнить `./install.sh --project <tmp-dir>` для полного набора плагинов и для выборочной установки, убедиться, что файлы попадают в ожидаемые пути внутри `.opencode/`.
- Проверить, что установка из `dist/.opencode/` даёт тот же результат по ключевым путям, что и установка через `install.sh`.
- Для `planning` и `brainstorm` проверить, что после установки доступны обновлённые команды, skills и вспомогательные скрипты.

**E2E / smoke**

- Временным проектом проверить наличие и читаемость ключевых файлов команд и skills после установки.
- Прогнать минимальные smoke-сценарии для `plan-make`, `brainstorm`, `review-pr`, `release-last-tag` на уровне статического наличия файлов и базовой исполнимости вспомогательных скриптов.

**CI acceptance**

- Успехом считается зелёный локальный прогон перенесённых test/quality checks и конфиг CI, который повторяет этот минимум на ветке с sync.
- Если какой-то upstream check не переносится в OpenCode-репозиторий, это должно быть отдельно зафиксировано в матрице `reject` с причиной и заменяющей проверкой или явным отсутствием замены.

**Негативные кейсы**

- Отсутствует optional tooling из upstream (`kitty`, `revdiff`, специфичные Claude hooks) — локальная версия не должна ломаться и должна иметь fallback или явный отказ.
- Не задан plugin data path / env — rule/script resolution не должен падать неочевидно.
- Пользователь ставит несуществующий plugin через `install.sh` — сценарий должен оставаться корректным.
- Часть upstream-функций не переносится в OpenCode — это должно быть явно задокументировано, а не проявляться как скрытая поломка.

## Риски и откаты (roll-back)

- Риск: слепой перенос upstream сломает локальные slug'и, русские тексты или OpenCode layout.
  Смягчение: вести матрицу `port/adapt/reject` и не смешивать механическое копирование с локальной адаптацией.

- Риск: Claude-only hooks и terminal-specific сценарии окажутся неприменимы в OpenCode.
  Смягчение: переносить такие части только после отдельной проверки; при несовместимости оставлять локальные аналоги и фиксировать отказ в отчёте.

- Риск: `dist/.opencode/**` разойдётся с `plugins/**`.
  Смягчение: обновлять `dist` отдельным шагом после каждого смыслового блока и проверять оба способа установки.

- Риск: перенос tests/CI выявит дополнительные дефекты в shell/python-файлах и растянет объём работ.
  Смягчение: включить quality-инфраструктуру в раннюю фазу, чтобы проблемы всплыли до массового портирования.

- Roll-back: выполнять синхронизацию по фазам и по модулям, чтобы можно было откатить отдельный блок без отмены всей работы.
- Roll-back: перед началом портирования сохранить baseline-ветку/тег локального состояния; при проблеме откатывать последнюю фазу целиком, начиная с repo-level infra, затем модульные изменения.
