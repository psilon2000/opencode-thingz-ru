---
name: release-new
description: "Провести релиз: определить следующий semver, собрать заметки с последнего тега, (опционально) обновить CHANGELOG и создать релиз на платформе (gh/glab/tea)."
argument-hint: "<тип релиза: patch/minor/major | или явная версия>"
---

# Новый релиз (semver + заметки)

Используй этот навык, когда нужно выпустить новую версию и показать пользователю безопасный preview до публикации.

В наборе доступны helper scripts:

- `.opencode/scripts/detect-platform.sh`
- `.opencode/scripts/calc-version.sh`
- `.opencode/scripts/get-notes.sh`

## Предусловия

- Репозиторий в git, есть теги формата `vX.Y.Z` (или `X.Y.Z`).
- Для публикации релиза:
  - GitHub: `gh` (желательно),
  - GitLab: `glab`,
  - Gitea: `tea`,
  - либо ручная публикация.

## Шаги

### 1) Определи платформу и последний тег

Если доступен helper script, сначала выполни:

```bash
bash .opencode/scripts/detect-platform.sh
```

Потом обнови теги и определи последний релизный тег:

```bash
git fetch origin --tags
git describe --tags --abbrev=0 --match "v*"
```

Если тега нет, считай что это первый релиз.

### 2) Уточни тип релиза

Спроси пользователя:
- `patch` (hotfix),
- `minor`,
- `major`,
- или «ввести версию вручную».

### 3) Посчитай следующую версию

Если доступен helper script, используй его:

```bash
bash .opencode/scripts/calc-version.sh <major|minor|hotfix>
```

Иначе посчитай вручную по semver.

### 4) Собери заметки релиза

Если доступен helper script, используй его:

```bash
bash .opencode/scripts/get-notes.sh <github|gitlab|gitea>
```

Он:
- берёт PR/MR после последнего тега, если доступны `gh`/`glab`/`tea` и `jq`,
- добавляет commits с последнего тега,
- группирует записи по типам (`feat`, `fix`, `refactor`, и т.д.).

Перед показом пользователю:
- убери дубли между PR и commits,
- предпочитай PR/MR запись, если описание совпадает,
- если grouping получился шумный — укороти вручную до полезного preview.

### 5) (Опционально) Обнови CHANGELOG

Если есть `CHANGELOG.md`:
- добавь новый раздел с версией и датой,
- вставь заметки,
- проверь формат.

### 6) Показать превью и подтвердить

Покажи пользователю:
- платформу (`github` / `gitlab` / `gitea`),
- последний тег,
- новый номер версии,
- список изменений (кратко),
- какие команды будешь выполнять (tag/push/release).

Без подтверждения **не публикуй**.

### 7) Создай тег и опубликуй

Минимум:

```bash
git tag -a "v<new>" -m "v<new>"
git push origin "v<new>"
```

GitHub release через `gh`:

```bash
gh release create "v<new>" --title "v<new>" --notes-file /tmp/release-notes.md
```

Если `gh`/`glab`/`tea` недоступен — оставь заметки для ручной публикации и явно скажи, что автоматическая публикация не выполнена.

## Выход

- Версия
- Заметки релиза (markdown)
- Выполненные команды (что реально было сделано)
