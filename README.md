# Vitral-icons

Tema de ícones para GNOME no Fedora, inspirado no visual do iOS e do macOS:
cada app com o seu logo colorido num tile de superelipse, todos com o mesmo
peso visual. Vem em duas versões, cada uma um tema completo e independente:

- **Vitral-icons** (escuro): tiles grafite de vidro, com borda de luz tingida
  pela cor do logo.
- **Vitral-icons-Light** (claro): tiles brancos com leve gradiente e borda
  sutil tingida; glifos que eram brancos sobre o tile viram grafite.

![Os dois temas: Vitral-icons à esquerda e Vitral-icons-Light à direita](docs/preview.png)

O que tem nos dois:

- **Apps:** o logo original de cada app (ou o do [Simple Icons](https://simpleicons.org))
  no tile; desenhos próprios, na paleta coral `#F0685A`, âmbar `#F5B53F` e
  menta `#4FC7A2`, para os apps do GNOME que não têm marca.
- **Pastas** no estilo do macOS, com emblema para Documentos, Downloads,
  Imagens, Músicas, Vídeos e as demais pastas especiais.
- **Tipos de arquivo:** folha dobrada com etiqueta colorida (DOC, XLS, PPT,
  PDF, IMG, MP3, MP4, TXT, código, ZIP, EXE).
- **Lugares e dispositivos:** lixeira (vazia e cheia), rede, servidor, discos,
  pendrive, fones, impressora, teclado, mouse e outros.
- **Tamanhos:** SVG escalável a partir de 96 px e PNGs otimizados de 16, 24, 32,
  48, 64, 128 e 256 px (nos pequenos a borda engrossa e o vidro simplifica).

Feito e testado no Fedora 45 com GNOME 51. Não precisa de nenhuma extensão.

## Instalar

Requer Python 3.11+, Pillow, PyGObject com librsvg, pycairo e o
`gtk-update-icon-cache` (tudo já vem no Fedora Workstation).

```sh
git clone https://github.com/viniciusbispo19/vitral-icons.git
cd vitral-icons
scripts/install.sh
```

O `install.sh` gera os dois temas em `~/.local/share/icons/Vitral-icons` e
`~/.local/share/icons/Vitral-icons-Light` e atualiza o cache de ícones de
cada um. Ele **não muda nenhuma configuração do GNOME**; para escolher o tema:

```sh
# escuro
gsettings set org.gnome.desktop.interface icon-theme 'Vitral-icons'
# claro
gsettings set org.gnome.desktop.interface icon-theme 'Vitral-icons-Light'
```

Ou deixe o próprio script aplicar: `scripts/install.sh --aplicar escuro` (ou
`--aplicar claro`). Também dá para escolher em Ajustes (GNOME Tweaks) >
Aparência > Ícones.

Opções do `install.sh`:

| Opção | O que faz |
| --- | --- |
| `--aplicar escuro\|claro` | Também define o tema de ícones do GNOME. |
| `--sem-servico` | Não instala o serviço que mantém os ícones atualizados. |
| `--dry-run` | Só mostra o que faria. |

### Apps instalados depois

O `install.sh` instala um serviço do systemd de usuário
(`vitral-icons.path`, `.service` e `.timer`). Quando um app é instalado ou
removido (RPM, Flatpak ou web app), os dois temas são regerados e o app novo
entra com o seu logo original no tile. À meia-noite, a data do ícone do
Calendário é atualizada.

### Ver a mudança

O GNOME troca os ícones na hora ao mudar o tema. Se depois de reinstalar algum
ícone continuar antigo, feche e abra o app; a dock e a grade de apps do GNOME
Shell só releem o tema quando você sai e entra de novo na sessão (no Wayland
não existe o Alt+F2 `r`).

Para refazer o cache à mão:

```sh
gtk-update-icon-cache -f -t ~/.local/share/icons/Vitral-icons
gtk-update-icon-cache -f -t ~/.local/share/icons/Vitral-icons-Light
```

## Desinstalar

```sh
scripts/uninstall.sh
```

Remove os dois temas e o serviço do systemd, e nada mais. Se um dos temas
estiver aplicado, o script mostra o comando para voltar ao padrão
(`gsettings reset org.gnome.desktop.interface icon-theme`).

## Ver antes de instalar

```sh
python3 icons/gerar.py --destino build --sem-cache
xdg-open preview.html
```

Gera os dois temas em `build/`, sem tocar no sistema, e monta um preview com
as duas versões lado a lado: todas as seções, os tamanhos pequenos em tamanho
real, pastas e tipos de arquivo de 16 a 96 px e de onde veio cada ícone. Com
`--folha`, também atualiza a imagem `docs/preview.png`.

## Estrutura

| Pasta / arquivo | O que tem |
| --- | --- |
| `config.toml` | Todas as variáveis: paleta, tamanhos, intensidades e as cores de cada variante. |
| `icons/gerar.py` | O gerador: lê o sistema, monta cada ícone uma vez e grava os dois temas. |
| `icons/tile.svg` | Template do tile (forma, vidro, borda, sombras), com marcadores preenchidos por variante. |
| `icons/glifos.py` | De onde vem cada ícone e os desenhos próprios (apps do GNOME, pastas, tipos de arquivo, dispositivos). |
| `icons/fontes/simple-icons/` | Logos do Simple Icons usados por alguns apps. |
| `scripts/install.sh`, `scripts/uninstall.sh` | Instalar e desinstalar os dois temas. |
| `scripts/systemd/` | Unidades do serviço que mantém os ícones atualizados. |
| `gerar.py` | Atalho para `icons/gerar.py` (é o que o serviço chama). |

As duas versões saem da mesma fonte: os desenhos e os logos são montados uma
vez e o gerador só troca as cores do tile, da borda e dos glifos. Não há SVG
escrito à mão para cada versão.

## Ajustar

Tudo fica em `config.toml`. Depois de editar, rode `scripts/install.sh` de
novo.

| Variável | Efeito |
| --- | --- |
| `[paleta]` | Coral, âmbar e menta dos desenhos próprios. |
| `icones.tile_lado`, `icones.avulsos_escala` | Tamanho dos ícones no quadro (120 = margem de 4). |
| `icones.area_alvo`, `icones.lado_maximo` | Peso visual do logo: fração da área do tile ocupada pela silhueta. |
| `icones.trash_style` | Lixeira `"tile"` ou `"avulsa"`. |
| `icones.tile`, `icones.tile_pequeno` | Borda, reflexo e sombras nos tamanhos grandes e até 32 px. |
| `icones.etiquetas` | Cor da etiqueta de cada tipo de arquivo. |
| `variantes.escura`, `variantes.clara` | Nome do tema, cores do tile, cor base e tingimento da borda (`tint_rim`), cores dos glifos, contorno do logo e as sobrescritas de `tile` e `tile_pequeno` de cada versão. |

Para mudar o desenho e não só os valores: `icons/tile.svg` (o tile) e
`icons/glifos.py` (de onde vem cada ícone: `original`, `simple:<marca>` ou
`desenho:<nome>`). Nos desenhos, a cor `tinta` é a dos glifos que ficam direto
sobre o tile: clara na versão escura e grafite na clara.

## Licença

Código e desenhos próprios: MIT, veja [LICENSE](LICENSE). Logos de marca e do
Simple Icons: veja [LICENCAS-TERCEIROS.md](LICENCAS-TERCEIROS.md).
