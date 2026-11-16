#!/usr/bin/env python3
"""Gerador do tema de ícones.

    python3 gerar.py                  gera o tema, atualiza o cache e cria preview.html
    python3 gerar.py --destino DIR    gera noutra pasta (padrão: ~/.local/share/icons/<NOME>)
    python3 gerar.py --sem-cache      não roda gtk-update-icon-cache
    python3 gerar.py --folha X.png    também salva uma folha de contato em PNG

De onde vem cada ícone está em glifos.py (original do app, Simple Icons ou
desenho próprio). Qualquer outro app visível, inclusive os instalados no
futuro, entra no mesmo padrão usando o ícone original do próprio app.

Não aplica o tema. Para aplicar:
    gsettings set org.gnome.desktop.interface icon-theme '<NOME_DO_TEMA>'

Requer: Python 3, Pillow (python3-pillow), PyGObject com Rsvg e pycairo.
"""
import base64
import html
import io
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import cairo
import gi
from PIL import Image, ImageDraw

gi.require_version("Rsvg", "2.0")
from gi.repository import Rsvg  # noqa: E402

NOME_DO_TEMA = "Brisa"

# Logo: lado do quadrado onde o conteúdo do logo é encaixado (~62% do tile
# de 112px) e tamanho máximo dos PNGs embutidos.
LADO_LOGO = 70
MAX_PNG = 256

AQUI = Path(__file__).resolve().parent
HOME = Path.home()
TEMPLATE = AQUI / "tile.svg"
PREVIEW = AQUI / "preview.html"
SIMPLE_ICONS_DIR = AQUI / "fontes/simple-icons"
CONTEXTOS = {"apps": "Applications", "places": "Places", "devices": "Devices"}


def _arg(nome, padrao=None):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


DESTINO = Path(_arg("--destino", HOME / ".local/share/icons" / NOME_DO_TEMA)).expanduser()
PASTA_SCALABLE = DESTINO / "scalable"

# Ordem de prioridade igual à do XDG: usuário antes do sistema.
PASTAS_DESKTOP = [
    HOME / ".local/share/applications",
    HOME / ".local/share/flatpak/exports/share/applications",
    Path("/var/lib/flatpak/exports/share/applications"),
    Path("/usr/share/applications"),
]
PASTAS_ICONES = [
    HOME / ".local/share/icons",
    HOME / ".local/share/flatpak/exports/share/icons",
    Path("/var/lib/flatpak/exports/share/icons"),
    Path("/usr/share/icons"),
]
PIXMAPS = Path("/usr/share/pixmaps")
GENERICO = Path("/usr/share/icons/Adwaita/scalable/mimetypes/application-x-executable.svg")

sys.path.insert(0, str(AQUI))
from glifos import APPS, DESENHOS, ICONES_FIXOS, SIMPLE_ICONS  # noqa: E402

SECOES = ["Dock", "Grade", "Sistema", "Utilitários", "Escritório", "Outros apps",
          "Automáticos", "Lugares", "Dispositivos"]
PASTAS_DA_GRADE = {"Sistema", "Utilitários", "Escritório"}


# ── Leitura do sistema ────────────────────────────────────────────────────
def ler_desktop(caminho):
    """Retorna as chaves (sem locale) da seção [Desktop Entry]."""
    chaves, dentro = {}, False
    for linha in caminho.read_text(errors="replace").splitlines():
        linha = linha.strip()
        if linha.startswith("["):
            dentro = linha == "[Desktop Entry]"
            continue
        if dentro and "=" in linha and not linha.startswith("#"):
            k, v = linha.split("=", 1)
            chaves.setdefault(k.strip(), v.strip())
    return chaves


def achar_desktop(desktop_id):
    for pasta in PASTAS_DESKTOP:
        p = pasta / desktop_id
        if p.is_file():
            return p
    return None


def logo_do_sistema():
    for linha in Path("/etc/os-release").read_text().splitlines():
        if linha.startswith("LOGO="):
            return linha.split("=", 1)[1].strip().strip('"')
    return None


def resolver(origem):
    """Devolve (nome_do_ícone, onde, problema)."""
    if origem == "os-release:LOGO":
        logo = logo_do_sistema()
        return (logo, "/etc/os-release (LOGO=)", None) if logo else (None, origem, "sem LOGO= no os-release")
    arq = achar_desktop(origem)
    if not arq:
        return None, origem, ".desktop não encontrado"
    icon = ler_desktop(arq).get("Icon", "")
    if not icon:
        return None, str(arq), "sem Icon="
    if icon.startswith("/"):
        return Path(icon).stem, str(arq), f"Icon= é caminho absoluto ({icon})"
    return icon, str(arq), None


def apps_visiveis():
    """Todos os .desktop visíveis (respeitando a prioridade usuário > sistema)."""
    vistos = {}
    for pasta in PASTAS_DESKTOP:
        if not pasta.is_dir():
            continue
        for arq in sorted(pasta.glob("*.desktop")):
            if arq.name not in vistos:
                vistos[arq.name] = ler_desktop(arq)
    return {
        nome: k for nome, k in vistos.items()
        if k.get("NoDisplay", "").lower() != "true"
        and k.get("Hidden", "").lower() != "true"
        and k.get("Type", "Application") == "Application"
        and ("GNOME" not in k.get("NotShowIn", ""))
        and (not k.get("OnlyShowIn") or "GNOME" in k.get("OnlyShowIn", ""))
    }


def corrigir_icones_absolutos():
    """Web apps (Brave/Chrome) gravam Icon= como caminho para um PNG no hicolor
    do usuário, o que nenhum tema consegue substituir. Troca pelo nome do ícone;
    o PNG continua lá e serve de reserva se o tema não tiver o ícone."""
    base = HOME / ".local/share/icons/hicolor"
    corrigidos = []
    pasta = HOME / ".local/share/applications"
    for arq in sorted(pasta.glob("*.desktop")) if pasta.is_dir() else []:
        texto = arq.read_text(errors="replace")
        novo = re.sub(
            rf"^Icon={re.escape(str(base))}/[^/\n]+/apps/([^/\n]+)\.(?:png|svg)$",
            r"Icon=\1", texto, flags=re.M)
        if novo != texto:
            arq.write_text(novo)
            corrigidos.append(arq.name)
    return corrigidos


def achar_original(nome):
    """O melhor ícone instalado do app: o SVG, senão o maior PNG."""
    candidatos = []
    for base in PASTAS_ICONES:
        hicolor = base / "hicolor"
        if not hicolor.is_dir():
            continue
        for tam in hicolor.iterdir():
            if tam.name.startswith("symbolic"):
                continue
            for ext in ("svg", "png"):
                p = tam / "apps" / f"{nome}.{ext}"
                if p.is_file():
                    candidatos.append(p)
    for ext in ("svg", "png"):
        p = PIXMAPS / f"{nome}.{ext}"
        if p.is_file():
            candidatos.append(p)

    def peso(p):
        if p.suffix == ".svg":
            return 10**9
        try:
            with Image.open(p) as im:
                return im.size[0] * im.size[1]
        except OSError:
            return 0

    return max(candidatos, key=peso) if candidatos else None


# ── Logos de marca ────────────────────────────────────────────────────────
def renderizar_svg(dados, lado=512):
    sup = cairo.ImageSurface(cairo.FORMAT_ARGB32, lado, lado)
    vp = Rsvg.Rectangle()
    vp.x = vp.y = 0
    vp.width = vp.height = lado
    Rsvg.Handle.new_from_data(dados).render_document(cairo.Context(sup), vp)
    sup.flush()
    return Image.frombuffer("RGBA", (lado, lado), bytes(sup.get_data()), "raw", "BGRa",
                            sup.get_stride(), 1)


def caixa(img):
    """Retângulo do conteúdo visível (ignora a margem transparente)."""
    return img.getchannel("A").point(lambda a: 255 if a > 12 else 0).getbbox()


def remover_placa(img, tolerancia=110):
    """Apaga a placa de fundo de um PNG: preenche a partir das bordas da placa
    tudo que tem a cor dela, e depois apaga a sombra e a franja translúcidas
    que ficam ligadas ao lado de fora."""
    img = img.copy()
    if max(img.size) > 512:
        img.thumbnail((512, 512), Image.LANCZOS)
    w, h = img.size
    px = img.load()
    sementes = []
    for x, y, dx, dy in ((w // 2, 0, 0, 1), (w // 2, h - 1, 0, -1), (0, h // 2, 1, 0), (w - 1, h // 2, -1, 0)):
        while 0 <= x < w and 0 <= y < h and px[x, y][3] < 230:
            x, y = x + dx, y + dy
        if 0 <= x < w and 0 <= y < h:
            sementes.append((x + dx * 3, y + dy * 3))
    if not sementes:
        return img
    cor_placa = px[sementes[0]]
    for s in sementes:
        if px[s][3] and sum(abs(a - b) for a, b in zip(px[s][:3], cor_placa[:3])) < tolerancia:
            ImageDraw.floodfill(img, s, (0, 0, 0, 0), thresh=tolerancia)
    # Sombra e franja: tudo translúcido ou da cor da placa ligado às bordas.
    def descartavel(p):
        r, g, b, a = p
        return a < 200 or (abs(r - cor_placa[0]) + abs(g - cor_placa[1])
                           + abs(b - cor_placa[2]) < tolerancia * 1.5)

    pilha = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    visto = set()
    while pilha:
        x, y = pilha.pop()
        if (x, y) in visto or not (0 <= x < w and 0 <= y < h) or not descartavel(px[x, y]):
            continue
        visto.add((x, y))
        px[x, y] = (0, 0, 0, 0)
        pilha += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return img


def imagem_no_tile(href, bbox, lado):
    """Posiciona uma imagem (lado x lado) para que o conteúdo dentro de bbox
    fique centrado num quadrado de LADO_LOGO."""
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    s = LADO_LOGO / max(w, h)
    x = 64 - (x0 + w / 2) * s
    y = 64 - (y0 + h / 2) * s
    t = lado * s
    return (f'<image x="{x:.2f}" y="{y:.2f}" width="{t:.2f}" height="{t:.2f}" '
            f'xlink:href="{href}" href="{href}"/>')


def logo_de_svg(dados):
    bbox = caixa(renderizar_svg(dados))
    href = "data:image/svg+xml;base64," + base64.b64encode(dados).decode()
    return imagem_no_tile(href, bbox, 512)


def logo_de_png(img):
    bbox = caixa(img)
    img = img.crop(bbox)
    img.thumbnail((MAX_PNG, MAX_PNG), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    href = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    lado = max(img.size)
    # Recentra a imagem recortada num quadrado virtual de lado x lado.
    dx, dy = (lado - img.size[0]) / 2, (lado - img.size[1]) / 2
    s = LADO_LOGO / lado
    return (f'<image x="{64 - LADO_LOGO / 2 + dx * s:.2f}" y="{64 - LADO_LOGO / 2 + dy * s:.2f}" '
            f'width="{img.size[0] * s:.2f}" height="{img.size[1] * s:.2f}" '
            f'xlink:href="{href}" href="{href}"/>')


def logo_original(arq, sem_fundo=False):
    if arq.suffix == ".svg" and not sem_fundo:
        return logo_de_svg(arq.read_bytes())
    img = renderizar_svg(arq.read_bytes()) if arq.suffix == ".svg" else Image.open(arq).convert("RGBA")
    if sem_fundo:
        img = remover_placa(img)
    return logo_de_png(img)


def logo_simple_icons(slug):
    cor, _ = SIMPLE_ICONS[slug]
    texto = (SIMPLE_ICONS_DIR / f"{slug}.svg").read_text()
    d = re.search(r'<path d="([^"]+)"', texto).group(1)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
           f'<path fill="{cor}" d="{d}"/></svg>')
    return logo_de_svg(svg.encode())


def montar_glifo(fonte, nome_icone):
    """Devolve (corpo do glifo, descrição da fonte)."""
    tipo, _, arg = fonte.partition(":")
    if tipo == "desenho":
        return DESENHOS[arg], "desenho próprio"
    if tipo == "solto":
        return DESENHOS[arg], "desenho próprio, sem tile"
    if tipo == "simple":
        _, licenca = SIMPLE_ICONS[arg]
        return logo_simple_icons(arg), f"Simple Icons: {arg} ({licenca})"
    arq = achar_original(nome_icone)
    if not arq:
        return None, f"original não encontrado para {nome_icone}"
    sem_fundo = tipo == "original-sem-fundo"
    descricao = "original do app" + (", placa de fundo removida" if sem_fundo else "")
    return logo_original(arq, sem_fundo), f"{descricao}: {arq}"


# ── Geração ───────────────────────────────────────────────────────────────
def montar(template, corpo, tile=True):
    corpo = "\n".join("    " + parte for parte in corpo.replace("><", ">\n<").splitlines())
    if not tile:
        template = re.sub(r"\s*<!-- tile:inicio.*?<!-- tile:fim -->", "", template, flags=re.S)
    # O marcador fica sozinho numa linha; o comentário do template não o repete.
    assert template.count("{{GLIFO}}") == 1, "tile.svg deve ter um único {{GLIFO}}"
    return template.replace("{{GLIFO}}", corpo)


def escrever_index():
    dirs = [f"scalable/{c}" for c in CONTEXTOS]
    secoes = "".join(
        f"\n[scalable/{c}]\nContext={ctx}\nSize=128\nMinSize=8\nMaxSize=512\nType=Scalable\n"
        for c, ctx in CONTEXTOS.items())
    (DESTINO / "index.theme").write_text(
        f"[Icon Theme]\nName={NOME_DO_TEMA}\n"
        "Comment=Tiles escuros de vidro com os logos coloridos dos apps\n"
        "Inherits=Adwaita,hicolor\nExample=org.gnome.Nautilus\n"
        f"Directories={','.join(dirs)}\n" + secoes)


def gerar():
    template = TEMPLATE.read_text()
    faltando = [f for _, _, f, _, _ in APPS + ICONES_FIXOS
                if f.split(":")[0] in ("desenho", "solto") and f.split(":", 1)[1] not in DESENHOS
                or f.startswith("simple:") and f[7:] not in SIMPLE_ICONS]
    if faltando:
        sys.exit(f"Fontes não definidas em glifos.py: {', '.join(faltando)}")

    # Monta tudo numa pasta nova e troca no fim, para o GNOME nunca ver o tema
    # pela metade (o serviço pode rodar com a sessão aberta).
    DESTINO.mkdir(parents=True, exist_ok=True)
    novo = DESTINO / ".scalable-novo"
    if novo.exists():
        shutil.rmtree(novo)
    for c in CONTEXTOS:
        (novo / c).mkdir(parents=True)

    itens, problemas, escritos = [], [], {}
    desktops_cobertos = set()

    def registrar(rotulo, secoes, fonte, nomes, contexto):
        corpo, descricao = montar_glifo(fonte, nomes[0])
        if corpo is None:
            problemas.append((rotulo, fonte, nomes[0], descricao, None))
            return
        svg = montar(template, corpo, tile=not fonte.startswith("solto:"))
        for nome in nomes:
            (novo / contexto / f"{nome}.svg").write_text(svg)
            escritos[nome] = rotulo
        itens.append({"rotulo": rotulo, "secoes": secoes, "fonte": descricao,
                      "nomes": nomes, "arquivo": f"scalable/{contexto}/{nomes[0]}.svg", "svg": svg})

    for rotulo, secoes, fonte, origens, extras in APPS:
        nomes = []
        for origem in origens:
            desktops_cobertos.add(origem)
            nome, onde, problema = resolver(origem)
            if problema:
                problemas.append((rotulo, origem, onde, problema, nome))
            if nome and nome not in nomes:
                nomes.append(nome)
        nomes += [e for e in extras if e not in nomes]
        if nomes:
            registrar(rotulo, secoes, fonte, nomes, "apps")

    for rotulo, secao, fonte, nomes, contexto in ICONES_FIXOS:
        registrar(rotulo, [secao], fonte, nomes, contexto)

    # Qualquer outro app visível: o logo original do próprio app no tile.
    for desktop_id, chaves in sorted(apps_visiveis().items()):
        icone = chaves.get("Icon", "")
        if desktop_id in desktops_cobertos or not icone or icone in escritos:
            continue
        rotulo = chaves.get("Name", desktop_id)
        if icone.startswith("/"):
            problemas.append((rotulo, desktop_id, str(achar_desktop(desktop_id)),
                              f"Icon= é caminho absoluto ({icone})", None))
            continue
        arq = achar_original(icone) or (GENERICO if GENERICO.is_file() else None)
        if not arq:
            problemas.append((rotulo, desktop_id, icone, "nenhum ícone original encontrado", None))
            continue
        svg = montar(template, logo_original(arq))
        (novo / "apps" / f"{icone}.svg").write_text(svg)
        escritos[icone] = rotulo
        itens.append({"rotulo": rotulo, "secoes": ["Automáticos"],
                      "fonte": f"original do app (automático): {arq}",
                      "nomes": [icone], "arquivo": f"scalable/apps/{icone}.svg", "svg": svg})

    if PASTA_SCALABLE.exists():
        velho = DESTINO / ".scalable-velho"
        if velho.exists():
            shutil.rmtree(velho)
        PASTA_SCALABLE.rename(velho)
        novo.rename(PASTA_SCALABLE)
        shutil.rmtree(velho)
    else:
        novo.rename(PASTA_SCALABLE)
    escrever_index()
    return itens, problemas, escritos


def atualizar_cache():
    subprocess.run(["gtk-update-icon-cache", "-f", "-t", str(DESTINO)], check=True)


# ── Preview ───────────────────────────────────────────────────────────────
def tipo_fonte(descricao):
    if descricao.startswith("desenho"):
        return "desenho"
    if descricao.startswith("Simple"):
        return "simple"
    return "original"


def escrever_preview(itens, problemas):
    def src(it):
        return html.escape(os.path.relpath(DESTINO / it["arquivo"], PREVIEW.parent))

    def cartao(it):
        nomes = ", ".join(it["nomes"])
        etiqueta = {"desenho": "desenho próprio", "simple": "Simple Icons",
                    "original": "original do app"}[tipo_fonte(it["fonte"])]
        return (f'<figure title="{html.escape(nomes)}&#10;{html.escape(it["fonte"])}">'
                f'<img src="{src(it)}" alt="{html.escape(it["rotulo"])}" loading="lazy">'
                f'<figcaption>{html.escape(it["rotulo"])}'
                f'<span class="fonte {tipo_fonte(it["fonte"])}">{etiqueta}</span></figcaption></figure>')

    def paineis(lista):
        grade = "".join(cartao(it) for it in lista)
        return (f'<div class="paineis"><div class="painel escuro"><div class="grade">{grade}</div></div>'
                f'<div class="painel claro"><div class="grade">{grade}</div></div></div>')

    blocos = []
    for secao in SECOES:
        lista = [it for it in itens if secao in it["secoes"]]
        if not lista:
            continue
        titulo = f"Pasta {secao}" if secao in PASTAS_DA_GRADE else secao
        blocos.append(f'<section><h2>{titulo} <small>{len(lista)}</small></h2>{paineis(lista)}</section>')

    linhas = "".join(
        f'<tr><td>{html.escape(it["rotulo"])}</td><td><code>{html.escape(", ".join(it["nomes"]))}</code></td>'
        f'<td><span class="fonte {tipo_fonte(it["fonte"])}">{html.escape(it["fonte"])}</span></td></tr>'
        for it in itens)
    blocos.append('<section><h2>De onde veio cada ícone</h2><div class="tabela"><table>'
                  '<thead><tr><th>App / ícone</th><th>Nome</th><th>Fonte</th></tr></thead>'
                  f'<tbody>{linhas}</tbody></table></div></section>')
    if problemas:
        lis = "".join(f"<li><b>{html.escape(r)}</b> — {html.escape(p)} <code>{html.escape(str(onde))}</code></li>"
                      for r, _, onde, p, _ in problemas)
        blocos.append(f'<section><h2>Sem mapeamento</h2><ul class="lista">{lis}</ul></section>')

    contagem = {t: sum(1 for it in itens if tipo_fonte(it["fonte"]) == t) for t in ("original", "simple", "desenho")}
    PREVIEW.write_text(f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NOME_DO_TEMA} preview</title>
<style>
  :root {{ --tam: 80px; --texto: #e8e8ec; --sutil: #8a8a93; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px 16px 64px; background: #0b0b0d; color: var(--texto);
         font: 14px/1.4 "Cantarell", "Inter", system-ui, sans-serif; }}
  header, section {{ max-width: 1400px; margin: 0 auto 28px; }}
  header {{ display: flex; flex-wrap: wrap; gap: 12px 24px; align-items: center; justify-content: space-between; }}
  h1 {{ margin: 0; font-size: 22px; }}
  h1 small, h2 small {{ color: var(--sutil); font-weight: 400; font-size: 14px; margin-left: 6px; }}
  h2 {{ font-size: 15px; font-weight: 600; margin: 0 0 10px; }}
  label {{ color: var(--sutil); }}
  .paineis {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  @media (max-width: 900px) {{ .paineis {{ grid-template-columns: 1fr; }} }}
  .painel {{ border-radius: 18px; padding: 16px 10px; }}
  .painel.escuro {{ background: #000; color: #f2f2f5; }}
  .painel.claro {{ background: #e9e9ee; color: #1b1b1f; }}
  .painel.claro .fonte {{ opacity: .8; }}
  .grade {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(calc(var(--tam) + 24px), 1fr)); gap: 14px 4px; }}
  figure {{ margin: 0; display: flex; flex-direction: column; align-items: center; text-align: center; }}
  figure img {{ width: var(--tam); height: var(--tam); }}
  figcaption {{ margin-top: 4px; font-size: 12px; line-height: 1.25; }}
  .fonte {{ display: block; font-size: 10px; margin-top: 2px; }}
  .fonte.original {{ color: #4FC7A2; }} .fonte.simple {{ color: #F5B53F; }} .fonte.desenho {{ color: #F0685A; }}
  .painel.claro .fonte.original {{ color: #1d7c60; }} .painel.claro .fonte.simple {{ color: #9a6400; }}
  .painel.claro .fonte.desenho {{ color: #b2332d; }}
  .tabela {{ overflow-x: auto; background: #151517; border-radius: 12px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  th, td {{ text-align: left; padding: 6px 12px; border-bottom: 1px solid #26262a; vertical-align: top; }}
  th {{ color: var(--sutil); font-weight: 600; }}
  td code {{ color: var(--sutil); font-size: 12px; word-break: break-all; }}
  td .fonte {{ font-size: 12px; word-break: break-all; }}
  .lista {{ background: #151517; border-radius: 12px; padding: 14px 14px 14px 32px; margin: 0; }}
</style>
</head>
<body>
<header>
  <h1>{NOME_DO_TEMA} <small>{len(itens)} ícones · {contagem["original"]} originais ·
    {contagem["simple"]} Simple Icons · {contagem["desenho"]} desenhos próprios</small></h1>
  <label>Tamanho <input id="tam" type="range" min="32" max="128" step="8" value="80"> <span id="tamv">80</span>px</label>
</header>
{''.join(blocos)}
<script>
  const tam = document.getElementById('tam'), tamv = document.getElementById('tamv');
  tam.addEventListener('input', () => {{
    document.documentElement.style.setProperty('--tam', tam.value + 'px'); tamv.textContent = tam.value; }});
</script>
</body>
</html>
""")


def salvar_folha(itens, destino, tam=96, colunas=10):
    """Folha de contato em PNG."""
    pad = 14
    linhas = (len(itens) + colunas - 1) // colunas
    sup = cairo.ImageSurface(cairo.FORMAT_ARGB32, colunas * (tam + pad) + pad, linhas * (tam + pad) + pad)
    ctx = cairo.Context(sup)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    for i, it in enumerate(itens):
        vp = Rsvg.Rectangle()
        vp.x, vp.y = pad + (i % colunas) * (tam + pad), pad + (i // colunas) * (tam + pad)
        vp.width = vp.height = tam
        Rsvg.Handle.new_from_data(it["svg"].encode()).render_document(ctx, vp)
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    sup.write_to_png(str(destino))


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    corrigidos = corrigir_icones_absolutos()
    itens, problemas, escritos = gerar()
    if "--sem-cache" not in sys.argv:
        atualizar_cache()
    escrever_preview(itens, problemas)
    if "--folha" in sys.argv:
        salvar_folha(itens, _arg("--folha"))

    print(f"{len(escritos)} SVGs em {PASTA_SCALABLE}")
    print(f"Preview: {PREVIEW}")
    for nome in corrigidos:
        print(f"Icon= absoluto trocado por nome em {nome}")
    print("\nFonte de cada ícone:")
    for it in itens:
        print(f"  - {it['rotulo']}: {it['fonte']}")
    if problemas:
        print("\nSem mapeamento:")
        for rotulo, origem, onde, problema, _ in problemas:
            print(f"  - {rotulo}: {problema}  [{onde}]")


if __name__ == "__main__":
    main()
