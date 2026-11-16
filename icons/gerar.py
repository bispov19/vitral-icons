#!/usr/bin/env python3
"""Gerador dos ícones do tema Brisa.

    python3 icons/gerar.py                 gera em ~/.local/share/icons/<nome> e atualiza o cache
    python3 icons/gerar.py --destino DIR   gera noutra pasta (ex.: build/), sem mexer no sistema
    python3 icons/gerar.py --sem-cache     não roda gtk-update-icon-cache
    python3 icons/gerar.py --sem-png       só o scalable (rápido, para testar desenhos)

Variáveis ajustáveis (paleta, área do logo, TINT_RIM, TRASH_STYLE, tamanhos)
ficam em config.toml, na raiz do projeto. De onde vem cada ícone (original do
app, Simple Icons ou desenho próprio) está em icons/glifos.py.

Não aplica o tema. Para aplicar:
    gsettings set org.gnome.desktop.interface icon-theme '<nome>'

Requer: Python 3.11+, Pillow, PyGObject com Rsvg e pycairo.
"""
import base64
import colorsys
import html
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import cairo
import gi
from PIL import Image, ImageDraw

gi.require_version("Rsvg", "2.0")
from gi.repository import Rsvg  # noqa: E402

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
CONFIG = tomllib.loads((RAIZ / "config.toml").read_text())
NOME_DO_TEMA = CONFIG["tema"]["nome"]
CFG = CONFIG["icones"]

HOME = Path.home()
TEMPLATE = AQUI / "tile.svg"
SIMPLE_ICONS_DIR = AQUI / "fontes/simple-icons"
LADO_LOGO = 70           # caixa inicial dos logos de marca, antes da normalização de área
TILE = 112               # lado do tile no quadro de 128
CONTEXTOS = {"apps": "Applications", "places": "Places", "devices": "Devices", "mimetypes": "MimeTypes"}


def _arg(nome, padrao=None):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


DESTINO_PADRAO = HOME / ".local/share/icons" / NOME_DO_TEMA
DESTINO = Path(_arg("--destino", DESTINO_PADRAO)).expanduser().resolve()
NO_SISTEMA = DESTINO == DESTINO_PADRAO.resolve()
PREVIEW = RAIZ / "preview.html"

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
from glifos import (APPS, CATEGORIAS, DESENHOS, ICONES_FIXOS, MIMETIPOS,  # noqa: E402
                    SIMBOLICOS, SIMPLE_ICONS, documento)

SECOES = ["Dock", "Grade", "Sistema", "Utilitários", "Escritório", "Outros apps",
          "Automáticos", "Lugares", "Pastas", "Tipos de arquivo", "Dispositivos"]
PASTAS_DA_GRADE = {"Sistema", "Utilitários", "Escritório"}


# ── Cores ─────────────────────────────────────────────────────────────────
def _rgb(hexa):
    hexa = hexa.lstrip("#")
    return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def misturar(a, b, t):
    """Mistura a cor a com b (t = 0 → a, t = 1 → b)."""
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def valores_paleta():
    pal = CONFIG["paleta"]
    v = {"GRAFITE_TOPO": pal["grafite_topo"], "GRAFITE_BASE": pal["grafite_base"]}
    for nome in ("coral", "ambar", "menta"):
        base, n = pal[nome], nome.upper()
        v[n] = base
        v[f"{n}_CLARO"] = misturar(base, "#FFFFFF", 0.3)
        v[f"{n}_FUNDO"] = misturar(base, "#000000", 0.1)
        v[f"{n}_ESCURO"] = misturar(base, "#000000", 0.1)
        v[f"{n}_ESCURO_FUNDO"] = misturar(base, "#000000", 0.3)
    return v


PALETA = valores_paleta()


# ── Template ──────────────────────────────────────────────────────────────
TEMPLATE_TEXTO = TEMPLATE.read_text()
assert TEMPLATE_TEXTO.count("{{GLIFO}}") == 1, "tile.svg deve ter um único marcador GLIFO"


def parametros(tamanho):
    """Valores do tile para um tamanho final em px (None = scalable)."""
    pequeno = CFG["tile_pequeno"]
    p = pequeno if tamanho and tamanho <= pequeno["ate_px"] else CFG["tile"]
    ref = tamanho or 128
    return {
        "BORDA_OPACIDADE": p["borda_opacidade"],
        # O traço é recortado pelo tile (só metade fica dentro): 2x a espessura.
        "BORDA_LARGURA": round(2 * p["borda_px"] * 128 / ref, 3),
        "REFLEXO": p["reflexo_opacidade"],
        "BRILHO": p["brilho_opacidade"],
        "BRILHO_MEIO": round(p["brilho_opacidade"] * 0.2, 3),
        "SOMBRA_INTERNA": p["sombra_interna"],
        "SOMBRA_CONTATO": p["sombra_contato"],
        "SOMBRA_LOGO": p["sombra_logo"],
    }


def montar(corpo, tile=True, borda="#FFFFFF", tamanho=None):
    valores = {**PALETA, **parametros(tamanho), "BORDA_COR": borda}
    svg = TEMPLATE_TEXTO
    if not tile:
        svg = re.sub(r"\s*<!-- tile:inicio.*?<!-- tile:fim -->", "", svg, flags=re.S)
    for k, v in valores.items():
        svg = svg.replace("{{" + k + "}}", str(v))
    corpo = "\n".join("    " + parte for parte in corpo.replace("><", ">\n<").splitlines())
    return svg.replace("{{GLIFO}}", corpo)


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
    if origem.startswith("icone:"):
        return origem[6:], "nome de ícone fixo", None
    arq = achar_desktop(origem)
    if not arq:
        return None, origem, ".desktop não instalado"
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


# ── Renderização e medidas ────────────────────────────────────────────────
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


def silhueta(img):
    """Área ocupada (com os buracos preenchidos) e a caixa do conteúdo."""
    w, h = img.size
    mascara = img.getchannel("A").point(lambda a: 255 if a > 40 else 0)
    bbox = mascara.getbbox()
    borda = Image.new("L", (w + 2, h + 2), 0)
    borda.paste(mascara, (1, 1))
    ImageDraw.floodfill(borda, (0, 0), 128)
    exterior = borda.histogram()[128]
    return (w + 2) * (h + 2) - exterior, bbox


def cor_principal(img):
    """Cor dominante do logo (matiz mais frequente entre os pixels saturados),
    ou None se o logo for neutro (branco, prata, preto)."""
    pequeno = img.resize((96, 96), Image.LANCZOS)
    baldes, opacos = {}, 0
    dados = pequeno.tobytes()
    for i in range(0, len(dados), 4):
        r, g, b, a = dados[i:i + 4]
        if a < 200:
            continue
        opacos += 1
        hh, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s < 0.3 or v < 0.25:
            continue
        balde = int(hh * 12) % 12
        baldes.setdefault(balde, []).append((r, g, b))
    if not baldes or opacos == 0:
        return None
    melhor = max(baldes.values(), key=len)
    if len(melhor) < 0.04 * opacos:
        return None
    return _hex(tuple(sum(c[i] for c in melhor) / len(melhor) for i in range(3)))


def normalizar(corpo):
    """Ajusta a escala do glifo para a silhueta ocupar `area_alvo` do tile,
    sem o maior lado passar de `lado_maximo`. Devolve (corpo, medidas)."""
    img = renderizar_svg(montar(corpo, tile=False, tamanho=None).replace(
        'filter="url(#sombra-logo)"', "").encode(), 256)
    area, bbox = silhueta(img)
    if not bbox:
        return corpo, {}
    escala_px = 256 / 128
    area_tile = (TILE * escala_px) ** 2
    antes = area / area_tile
    x0, y0, x1, y1 = (v / escala_px for v in bbox)
    lado = max(x1 - x0, y1 - y0)
    k = math.sqrt(CFG["area_alvo"] / antes) if antes > 0 else 1
    k = min(k, CFG["lado_maximo"] * TILE / lado)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    corpo = f'<g transform="translate(64 64) scale({k:.4f}) translate({-cx:.2f} {-cy:.2f})">{corpo}</g>'
    return corpo, {"area_antes": antes, "area_depois": antes * k * k, "escala": k}


# ── Logos de marca ────────────────────────────────────────────────────────
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
    maximo = CFG["max_png_embutido"]
    img.thumbnail((maximo, maximo), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    href = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    lado = max(img.size)
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
    """Devolve (corpo, descrição da fonte, tem_tile)."""
    tipo, _, arg = fonte.partition(":")
    if tipo == "lixeira":
        tipo = "desenho" if CFG["trash_style"] == "tile" else "solto"
    if tipo == "desenho":
        return DESENHOS[arg], "desenho próprio", True
    if tipo == "solto":
        return DESENHOS[arg], "desenho próprio, avulso (sem tile)", False
    if tipo == "documento":
        return documento(arg, CONFIG["icones"]["etiquetas"][arg]), f"desenho próprio (tipo de arquivo: {arg})", False
    if tipo == "simple":
        _, licenca = SIMPLE_ICONS[arg]
        return logo_simple_icons(arg), f"Simple Icons: {arg} ({licenca})", True
    arq = achar_original(nome_icone)
    if not arq:
        return None, f"original não encontrado para {nome_icone}", True
    sem_fundo = tipo == "original-sem-fundo"
    descricao = "original do app" + (", placa de fundo removida" if sem_fundo else "")
    return logo_original(arq, sem_fundo), f"{descricao}: {arq}", True


# ── Geração ───────────────────────────────────────────────────────────────
def escrever_index(destino, tamanhos):
    dirs, secoes = [], []
    for t in tamanhos:
        for c, ctx in CONTEXTOS.items():
            dirs.append(f"{t}x{t}/{c}")
            secoes.append(f"[{t}x{t}/{c}]\nContext={ctx}\nSize={t}\nType=Fixed\n")
    for c, ctx in CONTEXTOS.items():
        dirs.append(f"scalable/{c}")
        secoes.append(f"[scalable/{c}]\nContext={ctx}\nSize=128\nMinSize={CFG['scalable_min']}\n"
                      "MaxSize=512\nType=Scalable\n")
    dirs.append("symbolic/ui")
    secoes.append("[symbolic/ui]\nContext=UI\nSize=16\nMinSize=8\nMaxSize=512\nType=Scalable\n")
    (destino / "index.theme").write_text(
        f"[Icon Theme]\nName={NOME_DO_TEMA}\n"
        "Comment=Tiles escuros de vidro com os logos coloridos dos apps\n"
        "Inherits=Adwaita,hicolor\nExample=org.gnome.Nautilus\n"
        f"Directories={','.join(dirs)}\n\n" + "\n".join(secoes))


def salvar_png(svg, caminho, tamanho):
    sup = cairo.ImageSurface(cairo.FORMAT_ARGB32, tamanho, tamanho)
    vp = Rsvg.Rectangle()
    vp.x = vp.y = 0
    vp.width = vp.height = tamanho
    Rsvg.Handle.new_from_data(svg.encode()).render_document(cairo.Context(sup), vp)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    sup.write_to_png(str(caminho))


def gerar():
    faltando = []
    for _, _, f, _, _ in APPS + ICONES_FIXOS:
        tipo, _, arg = f.partition(":")
        if tipo in ("desenho", "solto", "lixeira") and arg not in DESENHOS \
                or tipo == "simple" and arg not in SIMPLE_ICONS:
            faltando.append(f)
    if faltando:
        sys.exit(f"Fontes não definidas em glifos.py: {', '.join(faltando)}")

    tamanhos = [] if "--sem-png" in sys.argv else CFG["tamanhos"]
    DESTINO.mkdir(parents=True, exist_ok=True)
    novo = DESTINO.parent / f".{DESTINO.name}-novo"
    if novo.exists():
        shutil.rmtree(novo)
    novo.mkdir()

    itens, problemas, escritos = [], [], {}
    desktops_cobertos = set()
    sem_normalizar = {f"desenho:{n}" for n in CFG["sem_normalizar"]}

    def gravar(rotulo, secoes, fonte_desc, corpo, nomes, contexto, tile=True, normaliza=True):
        medidas, borda = {}, "#FFFFFF"
        if tile:
            if normaliza:
                corpo, medidas = normalizar(corpo)
            principal = cor_principal(renderizar_svg(montar(corpo, tile=False).encode(), 256))
            if principal:
                borda = misturar("#FFFFFF", principal, CFG["tint_rim"])
        svg = montar(corpo, tile, borda)
        for nome in nomes:
            (novo / "scalable" / contexto).mkdir(parents=True, exist_ok=True)
            (novo / "scalable" / contexto / f"{nome}.svg").write_text(svg)
            escritos[nome] = rotulo
        for t in tamanhos:
            svg_t = montar(corpo, tile, borda, t)
            primeiro = novo / f"{t}x{t}" / contexto / f"{nomes[0]}.png"
            salvar_png(svg_t, primeiro, t)
            for nome in nomes[1:]:
                shutil.copyfile(primeiro, primeiro.with_name(f"{nome}.png"))
        itens.append({"rotulo": rotulo, "secoes": secoes, "fonte": fonte_desc, "nomes": nomes,
                      "contexto": contexto, "arquivo": f"scalable/{contexto}/{nomes[0]}.svg",
                      "borda": borda, "medidas": medidas, "svg": svg})

    def registrar(rotulo, secoes, fonte, nomes, contexto):
        corpo, descricao, tile = montar_glifo(fonte, nomes[0])
        if corpo is None:
            problemas.append((rotulo, fonte, nomes[0], descricao))
            return
        gravar(rotulo, secoes, descricao, corpo, nomes, contexto, tile, fonte not in sem_normalizar)

    for rotulo, secoes, fonte, origens, extras in APPS:
        nomes, ok = [], False
        for origem in origens:
            desktops_cobertos.add(origem)
            nome, onde, problema = resolver(origem)
            if problema and not (problema == ".desktop não instalado" and len(origens) > 1):
                problemas.append((rotulo, origem, onde, problema))
            if nome and nome not in nomes:
                nomes.append(nome)
        nomes += [e for e in extras if e not in nomes]
        if nomes:
            registrar(rotulo, secoes, fonte, nomes, "apps")

    for rotulo, secao, fonte, nomes, contexto in ICONES_FIXOS:
        registrar(rotulo, [secao], fonte, nomes, contexto)

    for categoria, nomes in MIMETIPOS.items():
        registrar(f"Tipo: {categoria}", ["Tipos de arquivo"], f"documento:{categoria}", nomes, "mimetypes")

    # Qualquer outro app visível: o logo original do próprio app no tile.
    for desktop_id, chaves in sorted(apps_visiveis().items()):
        icone = chaves.get("Icon", "")
        if desktop_id in desktops_cobertos or not icone or icone in escritos:
            continue
        rotulo = chaves.get("Name", desktop_id)
        if icone.startswith("/"):
            problemas.append((rotulo, desktop_id, str(achar_desktop(desktop_id)),
                              f"Icon= é caminho absoluto ({icone})"))
            continue
        arq = achar_original(icone) or (GENERICO if GENERICO.is_file() else None)
        if not arq:
            problemas.append((rotulo, desktop_id, icone, "nenhum ícone original encontrado"))
            continue
        gravar(rotulo, ["Automáticos"], f"original do app (automático): {arq}",
               logo_original(arq), [icone], "apps")

    # Simbólicos próprios (botões de janela); o resto vem do Adwaita.
    (novo / "symbolic/ui").mkdir(parents=True)
    for nome, svg in SIMBOLICOS.items():
        (novo / "symbolic/ui" / f"{nome}.svg").write_text(svg)

    escrever_index(novo, tamanhos)
    # Troca a pasta inteira de uma vez, para o GNOME nunca ver o tema pela metade.
    if DESTINO.exists():
        velho = DESTINO.parent / f".{DESTINO.name}-velho"
        if velho.exists():
            shutil.rmtree(velho)
        DESTINO.rename(velho)
        novo.rename(DESTINO)
        shutil.rmtree(velho)
    else:
        novo.rename(DESTINO)
    return itens, problemas, escritos


def atualizar_cache():
    subprocess.run(["gtk-update-icon-cache", "-f", "-t", str(DESTINO)], check=True)


# ── Preview da Fase 1 ─────────────────────────────────────────────────────
def versoes():
    def rodar(*cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return "?"
    rpm = rodar("rpm", "-q", "--qf", "%{NAME} %{VERSION}\\n", "libadwaita", "gtk4", "gtk3", "librsvg2")
    return [rodar("gnome-shell", "--version")] + rpm.splitlines()


def tipo_fonte(descricao):
    if descricao.startswith("desenho"):
        return "desenho"
    if descricao.startswith("Simple"):
        return "simple"
    return "original"


def antes_da_normalizacao(fonte, nome):
    """SVG do glifo sem a normalização de área (só para o comparativo)."""
    corpo, _, _ = montar_glifo(fonte, nome)
    return montar(corpo)


def escrever_preview(itens, problemas):
    def src(it, tamanho=None):
        if tamanho:
            alvo = DESTINO / f"{tamanho}x{tamanho}" / it["contexto"] / f"{it['nomes'][0]}.png"
        else:
            alvo = DESTINO / it["arquivo"]
        return html.escape(os.path.relpath(alvo, PREVIEW.parent))

    etiquetas = {"desenho": "desenho próprio", "simple": "Simple Icons", "original": "original do app"}

    def cartao(it):
        t = tipo_fonte(it["fonte"])
        return (f'<figure title="{html.escape(", ".join(it["nomes"]))}&#10;{html.escape(it["fonte"])}">'
                f'<img src="{src(it)}" alt="" loading="lazy"><figcaption>{html.escape(it["rotulo"])}'
                f'<span class="fonte {t}">{etiquetas[t]}</span></figcaption></figure>')

    def tres_fundos(lista):
        grade = "".join(cartao(it) for it in lista)
        return "".join(f'<div class="painel" style="background:{bg}"><span class="bg">{nome}</span>'
                       f'<div class="grade">{grade}</div></div>'
                       for bg, nome in (("#000", "#000"), ("#151517", "#151517"), ("#e9e9ee", "claro")))

    por_rotulo = {it["rotulo"]: it for it in itens}
    blocos = []

    # 1. Peso visual (casos de teste)
    linhas = []
    for rotulo, fonte, nome in (("Fedora", "original", "fedora-logo-icon"), ("Brave", "simple:brave", "brave-origin"),
                                ("Arquivos", "desenho:arquivos", "org.gnome.Nautilus"),
                                ("Spotify", "original", "spotify"), ("VS Code", "original", "vscode")):
        it = por_rotulo.get(rotulo)
        if not it:
            continue
        antes = "data:image/svg+xml;base64," + base64.b64encode(antes_da_normalizacao(fonte, nome).encode()).decode()
        m = it["medidas"]
        linhas.append(f'<div class="caso"><img src="{antes}" alt=""><img src="{src(it)}" alt="">'
                      f'<b>{rotulo}</b><span>{m.get("area_antes", 0) * 100:.0f}% → {m.get("area_depois", 0) * 100:.0f}%'
                      f' da área · escala {m.get("escala", 1):.2f}</span></div>')
    blocos.append('<section><h2>Peso visual igual <small>antes e depois da normalização por área '
                  f'(alvo {CFG["area_alvo"] * 100:.0f}%, maior lado até {CFG["lado_maximo"] * 100:.0f}% do tile)</small></h2>'
                  f'<div class="casos">{"".join(linhas)}</div></section>')

    # 2. Grades em três fundos
    for secao in SECOES:
        lista = [it for it in itens if secao in it["secoes"]]
        if not lista:
            continue
        titulo = f"Pasta {secao}" if secao in PASTAS_DA_GRADE else secao
        blocos.append(f'<section><h2>{titulo} <small>{len(lista)}</small></h2>'
                      f'<div class="tres">{tres_fundos(lista)}</div></section>')

    # 3. Tamanhos pequenos (PNGs reais, 1:1)
    amostra = [it for it in itens if it["rotulo"] in (
        "Fedora", "Arquivos", "Brave", "Spotify", "VS Code", "Firefox", "Calculadora", "Configurações",
        "Terminal", "Pasta", "Documentos", "Downloads", "Lixeira", "Tipo: pdf", "Tipo: planilha", "Tipo: codigo")]
    if (DESTINO / "16x16").exists():
        linhas = "".join(
            f'<div class="linha-tam" style="background:{bg}"><span class="bg">{nome}</span>'
            + "".join(f'<div class="tam"><span>{t}px</span>'
                      + "".join(f'<img src="{src(it, t)}" width="{t}" height="{t}" alt="">' for it in amostra)
                      + "</div>" for t in (16, 32, 48)) + "</div>"
            for bg, nome in (("#151517", "escuro"), ("#e9e9ee", "claro")))
        blocos.append('<section><h2>Tamanhos pequenos <small>PNGs otimizados de 16, 32 e 48 px, em tamanho real '
                      f'(borda {CFG["tile_pequeno"]["borda_opacidade"] * 100:.0f}% e sem reflexo até '
                      f'{CFG["tile_pequeno"]["ate_px"]} px)</small></h2>{linhas}</section>')

    # 4. Pastas e tipos de arquivo em vários tamanhos
    docs = [it for it in itens if it["secoes"][0] in ("Pastas", "Tipos de arquivo")]
    if (DESTINO / "16x16").exists():
        linhas = "".join(
            f'<div class="escada"><b>{html.escape(it["rotulo"])}</b>'
            f'<img src="{src(it)}" width="96" height="96" alt="">'
            + "".join(f'<img src="{src(it, t)}" width="{t}" height="{t}" alt="">' for t in (64, 48, 32, 24, 16))
            + "</div>" for it in docs)
        blocos.append(f'<section><h2>Pastas e tipos de arquivo <small>96, 64, 48, 32, 24 e 16 px</small></h2>'
                      f'<div class="escadas">{linhas}</div></section>')

    # 5. Simbólicos próprios
    simb = "".join(
        f'<div class="painel-simb" style="background:{bg};color:{fg}">'
        + "".join(f'<span class="simb" style="-webkit-mask-image:url({html.escape(os.path.relpath(DESTINO / "symbolic/ui" / (n + ".svg"), PREVIEW.parent))});'
                  f'mask-image:url({html.escape(os.path.relpath(DESTINO / "symbolic/ui" / (n + ".svg"), PREVIEW.parent))})" title="{n}"></span>'
                  for n in SIMBOLICOS)
        + "</div>" for bg, fg in (("#151517", "#f2f2f5"), ("#e9e9ee", "#1c1c20")))
    blocos.append(f'<section><h2>Simbólicos próprios <small>{", ".join(SIMBOLICOS)}</small></h2>'
                  f'<div class="simbs">{simb}</div></section>')

    # 6. Relatório
    linhas = "".join(
        f'<tr><td>{html.escape(it["rotulo"])}</td><td><code>{html.escape(", ".join(it["nomes"]))}</code></td>'
        f'<td><span class="fonte {tipo_fonte(it["fonte"])}">{html.escape(it["fonte"])}</span></td>'
        f'<td><span class="amostra" style="background:{it["borda"]}"></span></td></tr>' for it in itens)
    blocos.append('<section><h2>De onde veio cada ícone</h2><div class="tabela"><table><thead><tr><th>App / ícone</th>'
                  f'<th>Nomes</th><th>Fonte</th><th>Borda</th></tr></thead><tbody>{linhas}</tbody></table></div></section>')
    if problemas:
        lis = "".join(f"<li><b>{html.escape(r)}</b>: {html.escape(p)} <code>{html.escape(str(onde))}</code></li>"
                      for r, _, onde, p in problemas)
        blocos.append(f'<section><h2>Sem mapeamento / avisos</h2><ul class="lista">{lis}</ul></section>')

    cont = {t: sum(1 for it in itens if tipo_fonte(it["fonte"]) == t) for t in ("original", "simple", "desenho")}
    PREVIEW.write_text(f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NOME_DO_TEMA} preview</title>
<style>
  :root {{ --tam: 72px; --texto: #e8e8ec; --sutil: #8a8a93; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px 16px 64px; background: #0b0b0d; color: var(--texto);
         font: 14px/1.4 "Adwaita Sans", "Cantarell", system-ui, sans-serif; }}
  header, section {{ max-width: 1500px; margin: 0 auto 28px; }}
  header {{ display: flex; flex-wrap: wrap; gap: 8px 24px; align-items: baseline; justify-content: space-between; }}
  h1 {{ margin: 0; font-size: 22px; }}
  h1 small, h2 small {{ color: var(--sutil); font-weight: 400; font-size: 13px; margin-left: 6px; }}
  h2 {{ font-size: 15px; font-weight: 600; margin: 0 0 10px; }}
  .versoes {{ color: var(--sutil); font-size: 12px; }}
  .tres {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }}
  @media (max-width: 1100px) {{ .tres {{ grid-template-columns: 1fr; }} }}
  .painel {{ border-radius: 16px; padding: 22px 8px 12px; position: relative; }}
  .bg {{ position: absolute; top: 6px; left: 12px; font-size: 11px; color: #888; }}
  .grade {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(calc(var(--tam) + 18px), 1fr)); gap: 10px 2px; }}
  figure {{ margin: 0; display: flex; flex-direction: column; align-items: center; text-align: center; }}
  figure img {{ width: var(--tam); height: var(--tam); }}
  figcaption {{ margin-top: 3px; font-size: 11px; line-height: 1.2; color: #9a9aa2; }}
  .fonte {{ display: block; font-size: 9.5px; }}
  .fonte.original {{ color: #4FC7A2; }} .fonte.simple {{ color: #F5B53F; }} .fonte.desenho {{ color: #F0685A; }}
  .casos {{ display: flex; flex-wrap: wrap; gap: 12px; }}
  .caso {{ background: #151517; border-radius: 14px; padding: 12px; display: grid;
           grid-template-columns: 96px 96px; gap: 4px 8px; }}
  .caso img {{ width: 96px; height: 96px; }}
  .caso b, .caso span {{ grid-column: 1 / 3; font-size: 12px; }} .caso span {{ color: var(--sutil); }}
  .linha-tam {{ border-radius: 14px; padding: 22px 12px 12px; margin-bottom: 8px; position: relative; }}
  .tam {{ display: flex; align-items: center; gap: 6px; margin: 4px 0; flex-wrap: wrap; }}
  .tam span {{ width: 44px; font-size: 11px; color: #888; }}
  .tam img {{ image-rendering: auto; }}
  .escadas {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); gap: 8px; }}
  .escada {{ background: #151517; border-radius: 12px; padding: 8px 10px; display: flex; align-items: end; gap: 6px; }}
  .escada b {{ width: 100%; font-size: 12px; font-weight: 500; position: absolute; }}
  .escada {{ position: relative; padding-top: 26px; }}
  .escada b {{ top: 6px; left: 10px; }}
  .simbs {{ display: flex; gap: 10px; flex-wrap: wrap; }}
  .painel-simb {{ border-radius: 12px; padding: 14px 18px; display: flex; gap: 18px; }}
  .simb {{ width: 32px; height: 32px; background: currentColor; mask-size: contain; -webkit-mask-size: contain; }}
  .tabela {{ overflow-x: auto; background: #151517; border-radius: 12px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 12.5px; }}
  th, td {{ text-align: left; padding: 5px 10px; border-bottom: 1px solid #26262a; vertical-align: top; }}
  th {{ color: var(--sutil); font-weight: 600; }}
  td code, td .fonte {{ font-size: 11.5px; word-break: break-all; }} td code {{ color: var(--sutil); }}
  .amostra {{ display: inline-block; width: 22px; height: 12px; border-radius: 3px; }}
  .lista {{ background: #151517; border-radius: 12px; padding: 14px 14px 14px 32px; margin: 0; }}
</style>
</head>
<body>
<header>
  <h1>{NOME_DO_TEMA} · Fase 1 <small>{len(itens)} ícones · {cont["original"]} originais ·
    {cont["simple"]} Simple Icons · {cont["desenho"]} desenhos próprios · TRASH_STYLE={CFG["trash_style"]} ·
    TINT_RIM={CFG["tint_rim"]}</small></h1>
  <span class="versoes">{" · ".join(html.escape(v) for v in versoes())}</span>
  <label>Tamanho <input id="tam" type="range" min="32" max="128" step="8" value="72"></label>
</header>
{''.join(blocos)}
<script>
  document.getElementById('tam').addEventListener('input', e =>
    document.documentElement.style.setProperty('--tam', e.target.value + 'px'));
</script>
</body>
</html>
""")


def salvar_relatorio(itens, problemas):
    dados = {
        "icones": [{"rotulo": it["rotulo"], "nomes": it["nomes"], "fonte": it["fonte"],
                    "borda": it["borda"], **{k: round(v, 4) for k, v in it["medidas"].items()}} for it in itens],
        "problemas": [{"rotulo": r, "origem": o, "onde": str(w), "problema": p} for r, o, w, p in problemas],
    }
    (DESTINO / "relatorio.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1))


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    # Mexer nos .desktop do usuário só quando instala de verdade no sistema.
    corrigidos = corrigir_icones_absolutos() if NO_SISTEMA else []
    itens, problemas, escritos = gerar()
    if "--sem-cache" not in sys.argv:
        atualizar_cache()
    salvar_relatorio(itens, problemas)
    escrever_preview(itens, problemas)

    print(f"{len(escritos)} nomes de ícone em {DESTINO}")
    print(f"Preview: {PREVIEW}")
    for nome in corrigidos:
        print(f"Icon= absoluto trocado por nome em {nome}")
    auto = [it for it in itens if "Automáticos" in it["secoes"]]
    print(f"Automáticos (sem mapeamento manual): {len(auto)}")
    for it in auto:
        print(f"  - {it['rotulo']}: {it['fonte']}")
    if problemas:
        print("Avisos:")
        for rotulo, _, onde, problema in problemas:
            print(f"  - {rotulo}: {problema}  [{onde}]")


if __name__ == "__main__":
    main()
