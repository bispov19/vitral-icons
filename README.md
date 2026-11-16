# Brisa

Tema de ícones para GNOME (feito no Fedora 45): tiles escuros de vidro com glifos
simples, de traço único, em branco ou numa das três cores da paleta —
coral `#F0685A`, âmbar `#F5B53F` e menta `#4FC7A2`.

![Preview do tema](docs/preview.png)

- **Tile:** squircle (raio de 22% com suavização estilo iOS), grafite em gradiente
  `#2B2B2E → #151517`, borda interna de 1px, brilho fino no topo e sombra interna leve.
- **Glifos:** redesenhados à mão em SVG, traço 6/128 com pontas redondas, ~60% do tile.
  Nada de logos oficiais copiados.
- **Cobertura:** apps, pastas e lugares, lixeira e dispositivos. Ícones symbolic e de
  tipos de arquivo vêm do Adwaita (`Inherits=Adwaita,hicolor`).
- **Apps novos ficam no padrão sozinhos:** um serviço do systemd vigia as pastas de
  aplicativos e regenera o tema quando algo é instalado ou removido.

## Instalar

```sh
git clone https://github.com/viniciusbispo19/brisa-icons.git
cd brisa-icons
./instalar.sh --aplicar
```

Requer Python 3 e `gtk-update-icon-cache` (já vêm no Fedora Workstation).
Sem `--aplicar`, o script só gera o tema; para ativar depois:

```sh
gsettings set org.gnome.desktop.interface icon-theme 'Brisa'
```

O tema é gerado em `~/.local/share/icons/Brisa/` e o `preview.html` na pasta do
repositório (abra no navegador para conferir tudo antes de aplicar).

## Como funciona

| Arquivo | Papel |
| --- | --- |
| `tile.svg` | Template do tile. **Mudar o estilo de todos os ícones = editar só este arquivo.** |
| `glifos.py` | Paleta, um glifo por app/lugar/dispositivo e o mapa app → `.desktop`. |
| `gerar.py` | Lê o `Icon=` real de cada `.desktop` instalado e grava os SVGs com esse nome. Para trocar o nome do tema, mude `NOME_DO_TEMA` no topo. |
| `systemd/` | `brisa-icons.path` vigia as pastas de apps; `brisa-icons.service` roda o gerador. |

Pastas de `.desktop` lidas, nesta ordem: `~/.local/share/applications`,
`~/.local/share/flatpak/exports/share/applications`,
`/var/lib/flatpak/exports/share/applications` e `/usr/share/applications`.

### Apps sem glifo desenhado

Qualquer app visível que não esteja em `glifos.py` ganha um tile automático no mesmo
padrão:

1. se o app tem um ícone `*-symbolic.svg`, ele é tingido com uma cor da paleta e
   centralizado no tile;
2. se não tem, vira um monograma com a inicial do nome.

A cor é escolhida de forma estável a partir do nome do ícone. Para dar a um app um
glifo próprio, desenhe-o em `GLIFOS` e adicione uma linha em `APPS`.

### Web apps

Brave e Chrome gravam o `Icon=` dos web apps como caminho absoluto para um PNG, o que
nenhum tema consegue substituir. O gerador troca esse caminho pelo nome do ícone em
`~/.local/share/applications` (o PNG continua lá como reserva).

## Comandos úteis

```sh
python3 gerar.py                     # regenera tudo
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

MIT, veja [LICENSE](LICENSE).
