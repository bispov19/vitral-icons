#!/usr/bin/env bash
# uninstall.sh — remove os arquivos instalados pelo install.sh.
#
#   scripts/uninstall.sh [--fase icones|gtk|shell|todas] [--dry-run] [--forcar]
#
#   icones  ~/.local/share/icons/Brisa e o serviço do systemd
#   gtk     ~/.local/share/themes/Brisa/gtk-3.0 e gtk-4.0
#   shell   ~/.local/share/themes/Brisa/gnome-shell
#
# Se o tema ainda estiver aplicado (existe ~/.config/brisa/backup.json), recusa
# e pede para rodar o revert.sh antes; --forcar remove mesmo assim.
# Idempotente: o que já não existe é ignorado.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/comum.sh"
FORCAR=0
ler_opcoes "$@"

if [ -e "$CONF/brisa/backup.json" ] && [ "$FORCAR" = 0 ]; then
    echo "O tema ainda está aplicado. Rode antes: $RAIZ/scripts/revert.sh" >&2
    echo "(ou use --forcar para remover os arquivos mesmo assim)" >&2
    exit 1
fi

remover() {
    if [ -e "$1" ] || [ -L "$1" ]; then
        echo "  remove $1"
        rodar rm -rf "$1"
    fi
}

if fase_ativa icones; then
    echo "==> Ícones"
    rodar_sistema systemctl --user disable --now $UNIDADES
    for unidade in $UNIDADES; do
        remover "$CONF/systemd/user/$unidade"
    done
    rodar_sistema systemctl --user daemon-reload
    remover "$ICONES_DIR"
fi

if fase_ativa gtk; then
    echo "==> Tema GTK"
    remover "$TEMA_DIR/gtk-3.0"
    remover "$TEMA_DIR/gtk-4.0"
    remover "$TEMA_DIR/index.theme"
fi

if fase_ativa shell; then
    echo "==> Tema do GNOME Shell"
    remover "$TEMA_DIR/gnome-shell"
fi

# A pasta do tema some quando fica vazia.
if [ -d "$TEMA_DIR" ] && [ -z "$(ls -A "$TEMA_DIR")" ]; then
    rodar rmdir "$TEMA_DIR"
fi

echo
if [ "$DRY" = 1 ]; then echo "Simulação: nada foi removido."; else echo "Removido."; fi
