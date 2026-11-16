#!/usr/bin/env bash
# revert.sh — desfaz o apply.sh: restaura os valores do gsettings e os CSS de
# ~/.config guardados em ~/.config/brisa/backup.json.
#
#   scripts/revert.sh [--dry-run]
#
# Não apaga os arquivos instalados (para isso, scripts/uninstall.sh).
# Idempotente: sem backup, não faz nada.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/comum.sh"
ler_opcoes "$@"

if [ "$DRY" = 1 ]; then
    python3 "$RAIZ/scripts/estado.py" restaurar --dry-run
else
    python3 "$RAIZ/scripts/estado.py" restaurar
fi
