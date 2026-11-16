#!/usr/bin/env bash
# apply.sh — aplica o tema Brisa (rode antes o install.sh da mesma fase).
#
#   scripts/apply.sh [--fase icones|gtk|botoes|shell|todas] [--dry-run] [--flatpak]
#
#   icones  icon-theme = Brisa
#   gtk     gtk-theme = Brisa, color-scheme = prefer-dark e o CSS do tema em
#           ~/.config/gtk-4.0/gtk.css (libadwaita) e ~/.config/gtk-3.0/gtk.css
#   botoes  botões à esquerda: button-layout = 'close,minimize,maximize:'
#   shell   tema do Shell pela extensão oficial User Themes
#   --flatpak  também deixa os apps Flatpak lerem o CSS do tema
#
# Antes de mudar qualquer coisa, guarda os valores atuais em
# ~/.config/brisa/backup.json (cada um só na primeira vez). scripts/revert.sh
# desfaz tudo. Idempotente.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/comum.sh"
FLATPAK=0
ler_opcoes "$@"
ESTADO="python3 $RAIZ/scripts/estado.py"
USER_THEME="user-theme@gnome-shell-extensions.gcampax.github.com"

# Guarda o valor atual e muda a chave.
definir() {
    local schema="$1" chave="$2" valor="$3"
    rodar $ESTADO chave "$schema" "$chave"
    echo "  $schema $chave: $(gsettings get "$schema" "$chave") -> '$valor'"
    rodar gsettings set "$schema" "$chave" "$valor"
}

# Copia um CSS do tema para ~/.config, guardando o original.
copiar_css() {
    local origem="$1" destino="$2"
    rodar $ESTADO arquivo "$destino"
    rodar mkdir -p "$(dirname "$destino")"
    echo "  $destino <- $origem"
    rodar cp --remove-destination "$origem" "$destino"
}

exige() {
    if [ ! -e "$1" ]; then
        echo "Falta $1. Rode antes: $RAIZ/scripts/install.sh --fase $2" >&2
        exit 1
    fi
}

if fase_ativa icones; then
    exige "$ICONES_DIR/index.theme" icones
    echo "==> Ícones"
    definir org.gnome.desktop.interface icon-theme "$NOME"
fi

if fase_ativa gtk; then
    exige "$TEMA_DIR/gtk-4.0/libadwaita.css" gtk
    echo "==> GTK (os apps já abertos mudam ao reabrir)"
    definir org.gnome.desktop.interface gtk-theme "$NOME"
    definir org.gnome.desktop.interface color-scheme prefer-dark
    copiar_css "$TEMA_DIR/gtk-4.0/libadwaita.css" "$CONF/gtk-4.0/gtk.css"
    copiar_css "$TEMA_DIR/gtk-3.0/gtk.css" "$CONF/gtk-3.0/gtk.css"
    if [ "$FLATPAK" = 1 ]; then
        rodar $ESTADO marca flatpak-override
        rodar_sistema flatpak override --user --filesystem=xdg-config/gtk-4.0:ro --filesystem=xdg-config/gtk-3.0:ro
    else
        echo "  (apps Flatpak: rode de novo com --flatpak para eles lerem o CSS do tema)"
    fi
fi

if fase_ativa botoes; then
    echo "==> Botões de janela à esquerda"
    definir org.gnome.desktop.wm.preferences button-layout 'close,minimize,maximize:'
fi

if fase_ativa shell; then
    exige "$TEMA_DIR/gnome-shell/gnome-shell.css" shell
    echo "==> GNOME Shell"
    if ! gsettings list-schemas | grep -qx org.gnome.shell.extensions.user-theme; then
        echo "  A extensão User Themes não está instalada. Instale e rode de novo:" >&2
        echo "    sudo dnf install gnome-shell-extension-user-theme" >&2
        exit 1
    fi
    if ! gsettings get org.gnome.shell enabled-extensions | grep -q "$USER_THEME"; then
        # Marca (em vez de guardar a lista toda) para o revert desligar só ela.
        rodar $ESTADO marca habilitou-user-theme
        rodar_sistema gnome-extensions enable "$USER_THEME"
    fi
    definir org.gnome.shell.extensions.user-theme name "$NOME"
fi

echo
if [ "$DRY" = 1 ]; then echo "Simulação: nada foi aplicado."; else echo "Aplicado. Para desfazer: $RAIZ/scripts/revert.sh"; fi
