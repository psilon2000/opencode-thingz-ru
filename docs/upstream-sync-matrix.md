# Upstream Sync Matrix

Baseline сравнения:

- Local `HEAD`: `7d4a969087a5ba3d14e333aaf5b64fbbec53c389`
- Upstream `umputun/cc-thingz@master`: `a8b3e56aa4eded1c0ed4f238e5f9dd897dbcf7a6`

## Статусы

- `port` — переносим почти без изменений
- `adapt` — переносим идею, но адаптируем под OpenCode/RU layout
- `reject` — осознанно не переносим в текущем sync-срезе
- `pending` — ещё не дошли до реализации

## Матрица

| Область | Локально | Upstream | Решение | Статус | Примечание |
| --- | --- | --- | --- | --- | --- |
| Repo-level tests | отсутствуют | `tests/**` | adapt | implemented | Берём shell tests для custom rules и запускаем их по локальным путям `plugins/*/opencode/**`. |
| Repo-level CI | отсутствует | `.github/workflows/ci.yml` | adapt | implemented | Сохраняем YAML/frontmatter, shellcheck и python smoke tests, но пути и набор проверок подгоняем под локальную структуру. |
| `planning` custom rules | отсутствуют | `plugins/planning/scripts/resolve-rules.sh` + references | adapt | implemented | Проектный override хранится в `.opencode/planning-rules.md`, глобальный — в `~/.config/opencode/planning-rules.md`. |
| `planning` command behavior | `plugins/planning/opencode/commands/plan-make.md` | `plugins/planning/commands/make.md` | adapt | implemented (partial) | Сохраняем локальный краткий OpenCode workflow, но добавляем custom rules и `Критерии готово` в шаблон. |
| `plan-review` custom rules | `plugins/planning/opencode/skills/plan-review/SKILL.md` | `plugins/planning/agents/plan-review.md` | adapt | implemented (partial) | Берём только логику дополнительных review criteria; Claude agent/frontmatter и plugin-specific tooling не переносим. |
| `planning` interactive hook | минимальный `plan-annotate.py` | `scripts/plan-review-hook.py`, overlay integration | reject | decided | Claude hook runtime и terminal overlay завязаны на другую модель плагинов; локально остаётся существующий `plan-annotate.py`. |
| `planning:exec` | отсутствует | `plugins/planning/skills/exec/**` | reject | decided | Требует Claude-specific workflow, subagents и VCS scripts; не переносится в этот первый срез. |
| `brainstorm` custom rules | отсутствуют | `plugins/brainstorm/scripts/resolve-rules.sh` + references | adapt | implemented | Та же двухуровневая схема, но с путями OpenCode. |
| `brainstorm` skill naming | `brainstorm-do` | `brainstorm` | adapt | pending | Пока сохраняем локальное имя skill, чтобы не смешивать sync содержания и rename API. |
| `review-pr` discussion handling | локальный skill без явного акцента на automated/inline review | upstream `plugins/review/skills/pr/SKILL.md` | adapt | implemented (partial) | Добавлены явные проверки inline comments и automated reviews. Worktree-heavy Claude workflow не переносится как есть. |
| `review` annotation script | минимальный `git-review.py` | большой overlay-aware script | reject | decided | Локальный скрипт уже рабочий для OpenCode; overlay/hook runtime из upstream не переносим. |
| `release-tools` helper scripts | отсутствуют | `detect-platform.sh`, `calc-version.sh`, `get-notes.sh` | adapt | implemented | Скрипты перенесены в `.opencode/scripts/**` и используются skill-описаниями. |
| `release-new` workflow | локальный skeleton | более подробный release workflow | adapt | implemented (partial) | Перенесены safe pieces: platform detect, version calc, release notes preview. Публикация всё ещё требует ручного подтверждения. |
| `skill-eval` forced hook | rule only | `hooks/skill-forced-eval-hook.sh` | reject | decided | Для OpenCode сохраняем rule-based подход. Жёсткий Claude hook не переносим. |
| `thinking-tools` dialectic/root-cause | локальные краткие skills | более подробные upstream skills | adapt | implemented | Обновлена структура reasoning и выходного формата без смены локальных имён skills. |
| `thinking-tools` ask-codex | отсутствует | `plugins/thinking-tools/skills/ask-codex/SKILL.md` | adapt | implemented | Добавлен новый optional skill `thinking-ask-codex` для второго мнения через `codex` CLI. |
| `workflow` skills | локальные краткие skills | более подробные upstream skills | adapt | implemented | Обновлены `clarify`, `learn`, `md-copy`, `txt-copy`, `wrong` без смены локальных имён. |

## Принятые решения

- Source of truth: `plugins/**`. После изменений в исходниках зеркалим их в `dist/.opencode/**`.
- Для OpenCode не переносим upstream-пути вида `.claude/**` и `$CLAUDE_PLUGIN_DATA/**` как есть. Их заменяет пара `.opencode/<rules-file>` и `~/.config/opencode/<rules-file>`.
- Любые Claude-only hooks и `planning:exec` пока не адаптируются, а фиксируются как `reject`, чтобы не прятать несовместимость в полурабочем коде.
- Для `skill-eval` сохраняем мягкий rule-based preflight вместо принудительного runtime hook.
- Для `review` и `planning` переносим логику анализа и safe shell/python improvements, но не переносим Claude-specific overlay/hook execution model.
