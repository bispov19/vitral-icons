#!/usr/bin/env bash
# uninstall.sh — remove os temas de ícones Vitral-icons e Vitral-icons-Light
# e o serviço do systemd que os mantém atualizados.
#
#   scripts/uninstall.sh [--dry-run]
#
# Remove só o que o install.sh instala:
#   ~/.local/share/icons/Vitral-icons
#   ~/.local/share/icons/Vitral-icons-Light
#   ~/.config/systemd/user/vitral-icons.{path,service,timer}
#
# Não muda nenhuma configuração do GNOME. Se um dos dois temas estiver
# aplicado, mostra o comando para voltar ao tema de ícones padrão.
# Idempotente: o que já não existe é ignorado.
set -euo pipefail

ICONES="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
UNIDADES_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIDADES="vitral-icons.path vitral-icons.service vitral-icons.timer"
TEMAS="Vitral-icons Vitral-icons-Light"
DRY=0

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY=1; shift ;;
        -h|--help) sed -n '2,/^set -e/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
        *) echo "Opção desconhecida: $1 (veja --help)" >&2; exit 2 ;;
    esac
done

rodar() {
    if [ "$DRY" = 1 ]; then printf '  [dry-run] %s\n' "$*"; else "$@"; fi
}

remover() {
    if [ -e "$1" ] || [ -L "$1" ]; then
        echo "  remove $1"
        rodar rm -rf -- "$1"
    fi
}

echo "==> Serviço do systemd"
existe=0
for unidade in $UNIDADES; do
    [ -e "$UNIDADES_DIR/$unidade" ] && existe=1
done
if [ "$existe" = 1 ]; then
    rodar systemctl --user disable --now $UNIDADES || true
    for unidade in $UNIDADES; do
        remover "$UNIDADES_DIR/$unidade"
    done
    remover "${XDG_DATA_HOME:-$HOME/.local/share}/systemd/timers/stamp-vitral-icons.timer"
    rodar systemctl --user daemon-reload
fi

echo "==> Temas de ícones"
for tema in $TEMAS; do
    remover "$ICONES/$tema"
done

echo
if [ "$DRY" = 1 ]; then echo "Simulação: nada foi removido."; else echo "Removido."; fi
atual=$(gsettings get org.gnome.desktop.interface icon-theme 2>/dev/null | tr -d "'" || true)
case " $TEMAS " in
    *" $atual "*)
        echo "O tema de ícones aplicado ainda é $atual. Para voltar ao padrão do GNOME:"
        echo "  gsettings reset org.gnome.desktop.interface icon-theme" ;;
esac
