#!/usr/bin/env bash
# install.sh — instala as partes do tema Brisa (sem aplicar nada).
#
#   scripts/install.sh [--fase icones|gtk|todas] [--dry-run]
#
#   icones  gera os ícones em ~/.local/share/icons/<nome>
#   gtk     gera o tema em ~/.local/share/themes/<nome> (GTK 3 e GTK 4) e copia o
#           CSS do libadwaita para ~/.config/gtk-4.0/gtk.css e o do GTK 3 para
#           ~/.config/gtk-3.0/gtk.css (é o que os apps Flatpak conseguem ler),
#           guardando backup do que já existir em ~/.config/brisa/backup/
#
# Idempotente: rodar de novo só atualiza os arquivos. Com --dry-run, só mostra
# o que faria. Para aplicar (gsettings), veja scripts/apply.sh.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOME=$(python3 -c "import tomllib; print(tomllib.load(open('$RAIZ/config.toml','rb'))['tema']['nome'])")
FASE="todas"
DRY=0
while [ $# -gt 0 ]; do
    case "$1" in
        --fase) FASE="$2"; shift 2 ;;
        --dry-run) DRY=1; shift ;;
        *) echo "Opção desconhecida: $1" >&2; exit 2 ;;
    esac
done

BACKUP="${XDG_CONFIG_HOME:-$HOME/.config}/brisa/backup"
MARCA="Brisa para apps"   # presente no topo dos CSS gerados pelo tema

rodar() {
    if [ "$DRY" = 1 ]; then printf '  [dry-run] %s\n' "$*"; else "$@"; fi
}

# Copia o CSS gerado para ~/.config/gtk-X.0/gtk.css, com backup do arquivo do
# usuário (só se ele não for um CSS do próprio Brisa).
instalar_css_usuario() {
    local origem="$1" destino="$2"
    rodar mkdir -p "$(dirname "$destino")"
    if [ -L "$destino" ] || { [ -e "$destino" ] && ! grep -q "$MARCA" "$destino"; }; then
        local copia
        copia="$BACKUP/$(basename "$(dirname "$destino")")-gtk.css.$(date +%Y%m%d-%H%M%S)"
        echo "==> Backup de $destino em $copia"
        rodar mkdir -p "$BACKUP"
        rodar mv "$destino" "$copia"
    fi
    echo "==> Copiando $origem para $destino"
    rodar cp "$origem" "$destino"
}

if [ "$FASE" = icones ] || [ "$FASE" = todas ]; then
    echo "==> Ícones em ~/.local/share/icons/$NOME"
    rodar python3 "$RAIZ/icons/gerar.py"
fi

if [ "$FASE" = gtk ] || [ "$FASE" = todas ]; then
    TEMA="${XDG_DATA_HOME:-$HOME/.local/share}/themes/$NOME"
    echo "==> Tema GTK em $TEMA"
    rodar python3 "$RAIZ/gtk/gerar.py" --destino "$TEMA"
    # Atenção: o libadwaita sempre lê ~/.config/gtk-4.0/gtk.css, então estas
    # cópias já mudam o visual dos apps na próxima vez que forem abertos.
    echo "    (as cópias abaixo já valem para os apps libadwaita e GTK 3 abertos depois)"
    instalar_css_usuario "$TEMA/gtk-4.0/libadwaita.css" "${XDG_CONFIG_HOME:-$HOME/.config}/gtk-4.0/gtk.css"
    instalar_css_usuario "$TEMA/gtk-3.0/gtk.css" "${XDG_CONFIG_HOME:-$HOME/.config}/gtk-3.0/gtk.css"
fi

if [ "$DRY" = 1 ]; then echo; echo "Simulação: nada foi instalado."; else echo; echo "Instalado."; fi
cat <<EOF
Para aplicar, rode você mesmo:
  gsettings set org.gnome.desktop.interface icon-theme '$NOME'
  gsettings set org.gnome.desktop.interface gtk-theme '$NOME'
  gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
  gsettings set org.gnome.desktop.wm.preferences button-layout 'close,minimize,maximize:'
Para os apps Flatpak lerem o CSS do tema:
  flatpak override --user --filesystem=xdg-config/gtk-4.0:ro --filesystem=xdg-config/gtk-3.0:ro
EOF
