#!/usr/bin/env bash
# Gera o tema e instala o serviço que mantém apps novos no padrão do tema.
#   ./instalar.sh            instala e gera
#   ./instalar.sh --aplicar  também define o tema como tema de ícones do GNOME
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
DEST="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
NOME=$(sed -n 's/^NOME_DO_TEMA = "\(.*\)"/\1/p' "$REPO/gerar.py")

mkdir -p "$DEST"
for unidade in brisa-icons.path brisa-icons.service; do
  sed -e "s|@HOME@|$HOME|g" -e "s|@GERADOR@|$REPO/gerar.py|g" \
    "$REPO/systemd/$unidade" > "$DEST/$unidade"
done
systemctl --user daemon-reload
systemctl --user enable --now brisa-icons.path
systemctl --user enable brisa-icons.service

python3 "$REPO/gerar.py"

if [[ "${1:-}" == "--aplicar" ]]; then
  gsettings set org.gnome.desktop.interface icon-theme "$NOME"
  echo "Tema '$NOME' aplicado."
else
  echo "Para aplicar: gsettings set org.gnome.desktop.interface icon-theme '$NOME'"
fi
