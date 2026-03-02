---
name: workflow-txt-copy
description: Скопировать простой текст (без markdown) в буфер обмена (через custom tool clipboard).
argument-hint: "<текст или 'last'>"
---

# Text → clipboard

1) Подготовь чистый текст без markdown-разметки.
2) Скопируй в буфер обмена через tool `clipboard` (если доступен).
3) Если tool недоступен — выведи текст и попроси пользователя скопировать вручную.
