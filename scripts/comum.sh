# comum.sh — funções compartilhadas pelos scripts do Brisa (não execute direto).
#
# Variáveis de ambiente úteis:
#   BRISA_TESTE=1   não chama systemctl, gnome-extensions nem flatpak (só mostra);
#                   usado para testar os scripts com um HOME e um dconf de mentira.

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOME=$(python3 -c "import tomllib; print(tomllib.load(open('$RAIZ/config.toml','rb'))['tema']['nome'])")
DADOS="${XDG_DATA_HOME:-$HOME/.local/share}"
CONF="${XDG_CONFIG_HOME:-$HOME/.config}"
ICONES_DIR="$DADOS/icons/$NOME"
TEMA_DIR="$DADOS/themes/$NOME"
UNIDADES="brisa-icons.path brisa-icons.service brisa-icons.timer"
DRY=0
FASE="todas"

# Executa o comando, ou só mostra no --dry-run.
rodar() {
    if [ "$DRY" = 1 ]; then printf '  [dry-run] %s\n' "$*"; else "$@"; fi
}

# Comandos que mexem na sessão real (serviços, extensões, Flatpak): no modo de
# teste só são mostrados.
rodar_sistema() {
    if [ "${BRISA_TESTE:-0}" = 1 ]; then printf '  [teste] %s\n' "$*"; else rodar "$@"; fi
}

fase_ativa() {
    [ "$FASE" = todas ] || [ "$FASE" = "$1" ]
}

ler_opcoes() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --fase) FASE="$2"; shift 2 ;;
            --dry-run) DRY=1; shift ;;
            --flatpak) FLATPAK=1; shift ;;
            --forcar) FORCAR=1; shift ;;
            -h|--help) sed -n '2,/^set -e/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
            *) echo "Opção desconhecida: $1 (veja --help)" >&2; exit 2 ;;
        esac
    done
}
