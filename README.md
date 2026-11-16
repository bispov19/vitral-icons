# Brisa

Tema de ícones para GNOME (feito no Fedora 45) no visual do iOS 26 em modo escuro:
cada app aparece com o seu logo colorido e reconhecível, grande e centralizado num
tile escuro de vidro.

![Preview do tema](docs/preview.png)

- **Tile:** superelipse de verdade (expoente 5, o squircle do iOS), grafite em
  gradiente `#2B2B2E → #151517`, borda interna de 1px a 18% de branco, brilho fino
  no topo e sombra interna leve.
- **Logo:** ocupa ~62% do tile, centralizado, com leve sombra projetada e sem
  contorno. Vem, nesta ordem, de:
  1. o **ícone original instalado** do próprio app (SVG ou o maior PNG), recortado
     ao conteúdo; quando o PNG traz uma placa de fundo, ela é removida;
  2. o logo do **[Simple Icons](https://simpleicons.org)** na cor oficial da marca,
     quando o original vem com fundo que não dá para separar;
  3. **desenhos próprios**, coloridos e com volume, para apps sem logo de marca
     (Arquivos, Configurações, Calculadora, Calendário, apps do GNOME), pastas,
     lixeira e dispositivos, usando coral `#F0685A`, âmbar `#F5B53F` e menta
     `#4FC7A2` com branco, prata e grafite.
- **Cobertura:** apps, pastas e lugares, lixeira e dispositivos. Ícones symbolic e de
  tipos de arquivo vêm do Adwaita (`Inherits=Adwaita,hicolor`).
- **Apps novos ficam no padrão sozinhos:** um serviço do systemd vigia as pastas de
  aplicativos e regenera o tema quando algo é instalado ou removido; o app novo entra
  com o seu logo original no tile.

## Instalar

```sh
git clone https://github.com/viniciusbispo19/brisa-icons.git
cd brisa-icons
./instalar.sh --aplicar
```

Requer Python 3, Pillow (`python3-pillow`), PyGObject com librsvg e pycairo, e
`gtk-update-icon-cache` (tudo já vem no Fedora Workstation).
Sem `--aplicar`, o script só gera o tema; para ativar depois:

```sh
gsettings set org.gnome.desktop.interface icon-theme 'Brisa'
```

O tema é gerado em `~/.local/share/icons/Brisa/` e o `preview.html` na pasta do
repositório (abra no navegador para conferir tudo antes de aplicar).

## Como funciona

| Arquivo | Papel |
| --- | --- |
| `tile.svg` | Template do tile e paleta dos desenhos. **Mudar o estilo de todos os ícones = editar só este arquivo.** |
| `glifos.py` | De onde vem cada ícone (`original`, `simple:<marca>` ou `desenho:<nome>`), os desenhos próprios e o mapa app → `.desktop`. |
| `gerar.py` | Lê o `Icon=` real de cada `.desktop` instalado, monta os SVGs com esse nome e lista a fonte de cada um. Para trocar o nome do tema, mude `NOME_DO_TEMA` no topo. |
| `fontes/simple-icons/` | Logos do Simple Icons usados, com as licenças em `LICENCA.md`. |
| `systemd/` | `brisa-icons.path` vigia as pastas de apps; `brisa-icons.service` roda o gerador. |

Pastas de `.desktop` lidas, nesta ordem: `~/.local/share/applications`,
`~/.local/share/flatpak/exports/share/applications`,
`/var/lib/flatpak/exports/share/applications` e `/usr/share/applications`.

### Apps novos

Qualquer app visível que não esteja em `glifos.py` entra automaticamente com o seu
ícone original recortado e centralizado no tile. Para trocar a fonte de um app (por
exemplo, usar o Simple Icons ou um desenho próprio), adicione uma linha em `APPS`.

### Web apps

Brave e Chrome gravam o `Icon=` dos web apps como caminho absoluto para um PNG, o que
nenhum tema consegue substituir. O gerador troca esse caminho pelo nome do ícone em
`~/.local/share/applications` (o PNG continua lá como reserva).

## Comandos úteis

```sh
python3 gerar.py                     # regenera tudo e lista a fonte de cada ícone
python3 gerar.py --folha docs/preview.png   # também salva a folha de contato
journalctl --user -u brisa-icons.service    # log do serviço automático
```

## Desinstalar

```sh
gsettings reset org.gnome.desktop.interface icon-theme
systemctl --user disable --now brisa-icons.path brisa-icons.service
rm ~/.config/systemd/user/brisa-icons.{path,service}
rm -r ~/.local/share/icons/Brisa
```

## Licença

Código e desenhos próprios: MIT, veja [LICENSE](LICENSE). Os logos de marca são
dos respectivos donos; os do Simple Icons seguem as licenças em
[fontes/simple-icons/LICENCA.md](fontes/simple-icons/LICENCA.md). Os ícones
originais dos apps são lidos do sistema na hora de gerar e não fazem parte do repositório.
