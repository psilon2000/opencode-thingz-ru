#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="${ROOT_DIR}/plugins"

usage() {
  cat <<'USAGE'
Использование:
  ./install.sh --project <path> [plugin1 plugin2 ...]
  ./install.sh --global [plugin1 plugin2 ...]

Примеры:
  ./install.sh --project .
  ./install.sh --global brainstorm review workflow

Если список плагинов не указан — устанавливаются все.
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

MODE=""
TARGET=""

case "$1" in
  --project)
    MODE="project"
    TARGET="${2:-}"
    if [[ -z "$TARGET" ]]; then
      echo "Ошибка: не указан путь проекта для --project"
      exit 1
    fi
    shift 2
    DEST="${TARGET%/}/.opencode"
    ;;
  --global)
    MODE="global"
    shift 1
    DEST="${HOME}/.config/opencode"
    ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage
    exit 1
    ;;
esac

if [[ ! -d "$PLUGINS_DIR" ]]; then
  echo "Ошибка: не найден каталог plugins/ рядом с install.sh"
  exit 1
fi

# Определяем, какие плагины ставить
if [[ $# -eq 0 ]]; then
  mapfile -t PLUGINS < <(find "$PLUGINS_DIR" -mindepth 1 -maxdepth 1 -type d -printf "%f\n" | sort)
else
  PLUGINS=("$@")
fi

mkdir -p "$DEST"

echo "Установка в: $DEST"
echo "Режим: $MODE"
echo

for p in "${PLUGINS[@]}"; do
  SRC="${PLUGINS_DIR}/${p}/opencode"
  if [[ ! -d "$SRC" ]]; then
    echo "Пропуск: plugin '${p}' не найден (ожидался ${SRC})"
    continue
  fi

  echo "→ Устанавливаю plugin: ${p}"
  # копируем содержимое opencode/ в DEST/
  mkdir -p "$DEST"
  cp -a "${SRC}/." "$DEST/"
done

echo
echo "Готово."
echo "Перезапустите OpenCode, если он был открыт."
