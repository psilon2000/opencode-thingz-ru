# release-tools

Минимальный набор для релиз-процесса.

Содержимое:
- `.opencode/skills/release-new/SKILL.md` — «провести релиз»: следующий semver, заметки, тег, релиз (при наличии `gh`/`glab`/`tea`).
- `.opencode/skills/release-last-tag/SKILL.md` — список коммитов после последнего тега.
- `.opencode/scripts/detect-platform.sh` — определить GitHub/GitLab/Gitea по `origin`.
- `.opencode/scripts/calc-version.sh` — посчитать следующую semver-версию.
- `.opencode/scripts/get-notes.sh` — собрать release notes из PR/MR и commits.

Примечание:
- Это «скелет» под доработку. В ваших условиях (GitHub/GitLab/Gitea, политика релизов) шаги удобно уточнить и автоматизировать.
