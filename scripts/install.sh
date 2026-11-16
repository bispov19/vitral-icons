#!/usr/bin/env bash
# install.sh — instala as partes do tema Brisa, sem aplicar nada.
#
#   scripts/install.sh [--fase icones|gtk|shell|todas] [--dry-run]
#
#   icones  gera os ícones em ~/.local/share/icons/Brisa e instala o serviço
#           do systemd que os regenera quando apps são instalados e à meia-noite
#           (para a data do Calendário)
#   gtk     gera o tema GTK 3 / GTK 4 em ~/.local/share/themes/Brisa
#   shell   gera o tema do GNOME Shell em ~/.local/share/themes/Brisa/gnome-shell
#
# Idempotente: rodar de novo só atualiza os arquivos. Nada muda no visual até
# você rodar scripts/apply.sh.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/comum.sh"
ler_opcoes "$@"

if fase_ativa icones; then
    echo "==> Ícones em $ICONES_DIR"
    rodar python3 "$RAIZ/icons/gerar.py" --destino "$ICONES_DIR"
    echo "==> Serviço que mantém apps novos e a data do Calendário no padrão"
    rodar mkdir -p "$CONF/systemd/user"
    for unidade in $UNIDADES; do
        if [ "$DRY" = 1 ]; then
            printf '  [dry-run] instala %s\n' "$CONF/systemd/user/$unidade"
        else
            sed -e "s|@HOME@|$HOME|g" -e "s|@GERADOR@|$RAIZ/gerar.py|g" \
                "$RAIZ/scripts/systemd/$unidade" > "$CONF/systemd/user/$unidade"
        fi
    done
    rodar_sistema systemctl --user daemon-reload
    rodar_sistema systemctl --user enable --now brisa-icons.path brisa-icons.timer
    rodar_sistema systemctl --user enable brisa-icons.service
fi

if fase_ativa gtk; then
    echo "==> Tema GTK em $TEMA_DIR"
    rodar python3 "$RAIZ/gtk/gerar.py" --destino "$TEMA_DIR"
fi

if fase_ativa shell; then
    echo "==> Tema do GNOME Shell em $TEMA_DIR/gnome-shell"
    rodar python3 "$RAIZ/shell/gerar.py" --destino "$TEMA_DIR"
fi

echo
if [ "$DRY" = 1 ]; then echo "Simulação: nada foi instalado."; else echo "Instalado."; fi
echo "Para aplicar (com backup do que existe hoje): $RAIZ/scripts/apply.sh --fase $FASE"
