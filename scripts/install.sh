#!/usr/bin/env bash
# install.sh — instala os temas de ícones Vitral-icons (escuro) e
# Vitral-icons-Light (claro) em ~/.local/share/icons.
#
#   scripts/install.sh [--aplicar escuro|claro] [--sem-servico] [--dry-run]
#
#   (sem opções)     gera os dois temas, atualiza o cache de ícones e instala
#                    o serviço que mantém os ícones em dia
#   --aplicar TEMA   também define o tema de ícones do GNOME (escuro ou claro);
#                    sem esta opção nenhuma configuração do GNOME é alterada
#   --sem-servico    não instala o serviço do systemd de usuário
#   --dry-run        só mostra o que faria
#
# O serviço (vitral-icons.path/.service/.timer) regera os dois temas quando um
# app é instalado ou removido, para o app novo entrar com o seu logo no tile, e
# à meia-noite, para a data do ícone do Calendário acompanhar o dia.
#
# Idempotente: rodar de novo só atualiza os arquivos.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ICONES="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
UNIDADES_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIDADES="vitral-icons.path vitral-icons.service vitral-icons.timer"
ESCURO="Vitral-icons"
CLARO="Vitral-icons-Light"
DRY=0
SERVICO=1
APLICAR=""

while [ $# -gt 0 ]; do
    case "$1" in
        --aplicar) APLICAR="${2:-}"; shift 2 || { echo "Falta o tema: --aplicar escuro|claro" >&2; exit 2; } ;;
        --sem-servico) SERVICO=0; shift ;;
        --dry-run) DRY=1; shift ;;
        -h|--help) sed -n '2,/^set -e/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
        *) echo "Opção desconhecida: $1 (veja --help)" >&2; exit 2 ;;
    esac
done
case "$APLICAR" in
    ""|escuro|claro) ;;
    *) echo "--aplicar aceita escuro ou claro (recebeu: $APLICAR)" >&2; exit 2 ;;
esac

rodar() {
    if [ "$DRY" = 1 ]; then printf '  [dry-run] %s\n' "$*"; else "$@"; fi
}

# Dependências: Python com Pillow, PyGObject (Rsvg) e pycairo, e o
# gtk-update-icon-cache (tudo já vem no Fedora Workstation).
if ! python3 -c 'import cairo, gi, PIL; gi.require_version("Rsvg", "2.0"); from gi.repository import Rsvg' 2>/dev/null; then
    echo "Faltam módulos do Python. No Fedora: sudo dnf install python3-pillow python3-gobject python3-cairo librsvg2" >&2
    exit 1
fi
if ! command -v gtk-update-icon-cache >/dev/null; then
    echo "Falta o gtk-update-icon-cache. No Fedora: sudo dnf install gtk-update-icon-cache" >&2
    exit 1
fi

echo "==> Gerando $ESCURO e $CLARO em $ICONES"
# O gerador grava os dois temas e roda o gtk-update-icon-cache em cada um.
rodar python3 "$RAIZ/icons/gerar.py" --destino "$ICONES"

if [ "$SERVICO" = 1 ]; then
    echo "==> Serviço que mantém apps novos e a data do Calendário no padrão"
    rodar mkdir -p "$UNIDADES_DIR"
    for unidade in $UNIDADES; do
        if [ "$DRY" = 1 ]; then
            printf '  [dry-run] instala %s\n' "$UNIDADES_DIR/$unidade"
        else
            sed -e "s|@HOME@|$HOME|g" -e "s|@GERADOR@|$RAIZ/gerar.py|g" \
                "$RAIZ/scripts/systemd/$unidade" > "$UNIDADES_DIR/$unidade"
        fi
    done
    rodar systemctl --user daemon-reload
    rodar systemctl --user enable --now vitral-icons.path vitral-icons.timer
    rodar systemctl --user enable vitral-icons.service
fi

if [ -n "$APLICAR" ]; then
    tema=$([ "$APLICAR" = claro ] && echo "$CLARO" || echo "$ESCURO")
    echo "==> Aplicando o tema de ícones $tema"
    rodar gsettings set org.gnome.desktop.interface icon-theme "$tema"
fi

echo
if [ "$DRY" = 1 ]; then echo "Simulação: nada foi instalado."; else echo "Instalado."; fi
if [ -z "$APLICAR" ]; then
    echo "Nenhuma configuração do GNOME foi alterada. Para aplicar:"
    echo "  escuro:  gsettings set org.gnome.desktop.interface icon-theme '$ESCURO'"
    echo "  claro:   gsettings set org.gnome.desktop.interface icon-theme '$CLARO'"
fi
