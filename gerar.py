#!/usr/bin/env python3
"""Gerador do tema de ícones.

    python3 gerar.py                 gera o tema, atualiza o cache e cria preview.html
    python3 gerar.py --sem-cache     não roda gtk-update-icon-cache
    python3 gerar.py --folha X.png   também salva uma folha de contato em PNG

Apps com glifo desenhado à mão estão em glifos.py. Qualquer outro app visível
(inclusive os instalados no futuro) ganha um tile automático no mesmo padrão:
o ícone symbolic do próprio app tingido com uma cor da paleta ou, se ele não
tiver symbolic, um monograma com a inicial do nome.

Não aplica o tema. Para aplicar:
    gsettings set org.gnome.desktop.interface icon-theme '<NOME_DO_TEMA>'
"""
import base64
import html
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

NOME_DO_TEMA = "Brisa"

AQUI = Path(__file__).resolve().parent
HOME = Path.home()
DESTINO = HOME / ".local/share/icons" / NOME_DO_TEMA
PASTA_SCALABLE = DESTINO / "scalable"
CONTEXTOS = {"apps": "Applications", "places": "Places", "devices": "Devices"}
TEMPLATE = AQUI / "tile.svg"
PREVIEW = AQUI / "preview.html"

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

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

sys.path.insert(0, str(AQUI))
from glifos import AMBAR, APPS, BRANCO, CORAL, GLIFOS, ICONES_FIXOS, MENTA  # noqa: E402

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
            if arq.name in vistos:
                continue
            k = ler_desktop(arq)
            vistos[arq.name] = k
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


# ── Geração ───────────────────────────────────────────────────────────────
def montar(template, cor, corpo):
    corpo = "\n".join("    " + parte for parte in corpo.replace("><", ">\n<").splitlines())
    return template.replace("{{COR}}", cor).replace("{{GLIFO}}", corpo)


def montar_svg(template, glifo):
    return montar(template, *GLIFOS[glifo])


def cor_automatica(chave):
    return [CORAL, AMBAR, MENTA, BRANCO][zlib.crc32(chave.encode()) % 4]


def achar_symbolic(nome):
    for base in PASTAS_ICONES:
        for sub in ("hicolor/symbolic/apps", "hicolor/scalable/apps"):
            p = base / sub / f"{nome}-symbolic.svg"
            if p.is_file():
                return p
    return None


SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"


def glifo_symbolic(arq, cor):
    """Embute o symbolic do app no quadro do glifo (64px, centrado) e o tinge
    com a cor da paleta preservando só a forma (canal alfa)."""
    try:
        raiz = ET.parse(arq).getroot()
    except ET.ParseError:
        return None
    viewbox = raiz.get("viewBox") or f"0 0 {raiz.get('width', '16').rstrip('px')} {raiz.get('height', '16').rstrip('px')}"

    # Remove tudo que não é SVG (metadados e extras do Inkscape) e prefixa ids
    # para não colidirem com os do template.
    def limpar(el):
        for filho in list(el):
            if not str(filho.tag).startswith("{%s}" % SVG_NS) or filho.tag.endswith("}metadata"):
                el.remove(filho)
            else:
                limpar(filho)
        for k in list(el.attrib):
            if k.startswith("{") and not k.startswith("{%s}" % XLINK_NS):
                del el.attrib[k]
            elif k == "id":
                el.attrib[k] = "sym-" + el.attrib[k]
            elif "url(#" in el.attrib[k]:
                el.attrib[k] = el.attrib[k].replace("url(#", "url(#sym-")
            elif k in ("href", "{%s}href" % XLINK_NS) and el.attrib[k].startswith("#"):
                el.attrib[k] = "#sym-" + el.attrib[k][1:]
        if el.get("style") and "url(#" in el.get("style"):
            el.set("style", el.get("style").replace("url(#", "url(#sym-"))

    limpar(raiz)
    corpo = "".join(ET.tostring(filho, encoding="unicode") for filho in raiz)
    return (
        '<defs><filter id="tingir" x="0" y="0" width="1" height="1" '
        'color-interpolation-filters="sRGB">'
        f'<feFlood flood-color="{cor}"/><feComposite in2="SourceAlpha" operator="in"/>'
        "</filter></defs>"
        '<g filter="url(#tingir)" fill="#000" stroke="none">'
        f'<svg x="32" y="32" width="64" height="64" viewBox="{viewbox}" overflow="visible">'
        f"{corpo}</svg></g>"
    )


def glifo_monograma(nome_do_app):
    letra = next((c for c in nome_do_app if c.isalnum()), "?").upper()
    return (f'<text x="64" y="87" text-anchor="middle" font-family="Cantarell, Inter, sans-serif" '
            f'font-size="66" font-weight="700" fill="currentColor" stroke="none">'
            f"{html.escape(letra)}</text>")


def glifo_automatico(icone, nome_do_app):
    """Devolve (cor, corpo, origem) para um app sem glifo desenhado."""
    cor = cor_automatica(icone)
    sym = achar_symbolic(icone)
    if sym:
        corpo = glifo_symbolic(sym, cor)
        if corpo:
            return cor, corpo, "symbolic"
    return cor, glifo_monograma(nome_do_app), "monograma"


def escrever_index():
    dirs = [f"scalable/{c}" for c in CONTEXTOS]
    secoes = "".join(
        f"\n[scalable/{c}]\nContext={ctx}\nSize=128\nMinSize=8\nMaxSize=512\nType=Scalable\n"
        for c, ctx in CONTEXTOS.items())
    (DESTINO / "index.theme").write_text(
        f"[Icon Theme]\nName={NOME_DO_TEMA}\n"
        "Comment=Tiles escuros de vidro com glifos simples\n"
        "Inherits=Adwaita,hicolor\nExample=org.gnome.Nautilus\n"
        f"Directories={','.join(dirs)}\n" + secoes)


def gerar():
    template = TEMPLATE.read_text()
    faltando = [g for _, _, g, _, _ in APPS + ICONES_FIXOS if g not in GLIFOS]
    if faltando:
        sys.exit(f"Glifos não definidos em glifos.py: {', '.join(faltando)}")

    # Monta tudo numa pasta nova e troca no fim, para o GNOME nunca ver o tema
    # pela metade (o serviço pode rodar com a sessão aberta).
    novo = DESTINO / ".scalable-novo"
    if novo.exists():
        shutil.rmtree(novo)
    for c in CONTEXTOS:
        (novo / c).mkdir(parents=True)

    itens, problemas, escritos = [], [], {}
    desktops_cobertos = set()
    for rotulo, secoes, glifo, origens, extras in APPS:
        nomes = []
        for origem in origens:
            desktops_cobertos.add(origem)
            nome, onde, problema = resolver(origem)
            if problema:
                problemas.append((rotulo, origem, onde, problema, nome))
            if nome and nome not in nomes:
                nomes.append(nome)
        nomes += [e for e in extras if e not in nomes]
        svg = montar_svg(template, glifo)
        for nome in nomes:
            (novo / "apps" / f"{nome}.svg").write_text(svg)
            escritos[nome] = rotulo
        itens.append({"rotulo": rotulo, "secoes": secoes, "glifo": glifo,
                      "nomes": nomes, "svg": svg})

    for rotulo, secao, glifo, nomes, contexto in ICONES_FIXOS:
        svg = montar_svg(template, glifo)
        for nome in nomes:
            (novo / contexto / f"{nome}.svg").write_text(svg)
            escritos[nome] = rotulo
        itens.append({"rotulo": rotulo, "secoes": [secao], "glifo": glifo,
                      "nomes": nomes, "svg": svg})

    # Qualquer outro app visível: tile automático no padrão do tema.
    for desktop_id, chaves in sorted(apps_visiveis().items()):
        icone = chaves.get("Icon", "")
        if desktop_id in desktops_cobertos or not icone or icone in escritos:
            continue
        rotulo = chaves.get("Name", desktop_id)
        if icone.startswith("/"):
            problemas.append((rotulo, desktop_id, str(achar_desktop(desktop_id)),
                              f"Icon= é caminho absoluto ({icone})", None))
            continue
        cor, corpo, origem = glifo_automatico(icone, rotulo)
        svg = montar(template, cor, corpo)
        (novo / "apps" / f"{icone}.svg").write_text(svg)
        escritos[icone] = rotulo
        itens.append({"rotulo": rotulo, "secoes": ["Automáticos"], "glifo": origem,
                      "nomes": [icone], "svg": svg})

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
def img(svg, alt):
    b64 = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" alt="{html.escape(alt)}">'


def escrever_preview(itens, problemas):
    def cartao(it):
        nomes = ", ".join(it["nomes"]) or "—"
        return (f'<figure title="{html.escape(nomes)}">{img(it["svg"], it["rotulo"])}'
                f'<figcaption>{html.escape(it["rotulo"])}<code>{html.escape(nomes)}</code>'
                f'</figcaption></figure>')

    blocos = []
    dock = [it for it in itens if "Dock" in it["secoes"]]
    blocos.append(
        '<section><h2>Dock</h2><div class="dock">'
        + "".join(f'<span title="{html.escape(it["rotulo"])}">{img(it["svg"], it["rotulo"])}</span>' for it in dock)
        + '</div><div class="grade">' + "".join(cartao(it) for it in dock) + "</div></section>")
    for secao in SECOES[1:]:
        lista = [it for it in itens if secao in it["secoes"]]
        if not lista:
            continue
        titulo = f"Pasta {secao}" if secao in PASTAS_DA_GRADE else secao
        blocos.append(f'<section><h2>{titulo} <small>{len(lista)}</small></h2>'
                      f'<div class="grade">' + "".join(cartao(it) for it in lista) + "</div></section>")

    if problemas:
        linhas = "".join(
            f"<li><b>{html.escape(r)}</b> — {html.escape(p)}<br><code>{html.escape(onde)}</code>"
            + (f"<br>SVG gerado como <code>{html.escape(n)}.svg</code>, mas só vale se o Icon= usar esse nome."
               if n else "") + "</li>"
            for r, _, onde, p, n in problemas)
        blocos.append(f'<section><h2>Sem mapeamento</h2><ul class="lista">{linhas}</ul></section>')

    PREVIEW.write_text(f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NOME_DO_TEMA} preview</title>
<style>
  :root {{ --tam: 96px; --fundo: #0e0e10; --texto: #e8e8ec; --sutil: #8a8a93; --painel: rgba(255,255,255,.04); }}
  body.claro {{ --fundo: #ececf0; --texto: #1b1b1f; --sutil: #66666f; --painel: rgba(0,0,0,.04); }}
  body.parede {{ --fundo: #1a2a3a; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px 16px 64px; background: var(--fundo); color: var(--texto);
         font: 14px/1.4 "Cantarell", "Inter", system-ui, sans-serif; transition: background .2s; }}
  body.parede {{ background: radial-gradient(120% 90% at 20% 10%, #4b6a8a 0%, #24324a 45%, #120f1c 100%) fixed; }}
  header {{ max-width: 1100px; margin: 0 auto 24px; display: flex; flex-wrap: wrap; gap: 16px;
           align-items: center; justify-content: space-between; }}
  h1 {{ margin: 0; font-size: 22px; font-weight: 700; }}
  .controles {{ display: flex; flex-wrap: wrap; gap: 12px; align-items: center; color: var(--sutil); }}
  .controles button {{ background: var(--painel); color: var(--texto); border: 1px solid rgba(127,127,127,.3);
                      border-radius: 8px; padding: 6px 12px; cursor: pointer; font: inherit; }}
  .controles button[aria-pressed=true] {{ border-color: #4FC7A2; }}
  section {{ max-width: 1100px; margin: 0 auto 32px; }}
  h2 {{ font-size: 15px; font-weight: 600; margin: 0 0 12px; }}
  h2 small {{ color: var(--sutil); font-weight: 400; margin-left: 6px; }}
  .dock {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; padding: 8px 10px; margin: 0 auto 20px;
           width: fit-content; max-width: 100%; border-radius: 24px; background: rgba(40,40,44,.55);
           border: 1px solid rgba(255,255,255,.12); backdrop-filter: blur(20px); }}
  .dock img {{ width: 56px; height: 56px; display: block; }}
  .grade {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(calc(var(--tam) + 40px), 1fr)); gap: 18px 8px; }}
  figure {{ margin: 0; display: flex; flex-direction: column; align-items: center; text-align: center; }}
  figure img {{ width: var(--tam); height: var(--tam); }}
  figcaption {{ margin-top: 6px; font-size: 13px; }}
  figcaption code {{ display: block; color: var(--sutil); font-size: 11px; word-break: break-all; }}
  .lista {{ background: var(--painel); border-radius: 12px; padding: 14px 14px 14px 32px; margin: 0; }}
  .lista li {{ margin: 4px 0; }}
  .lista code {{ color: var(--sutil); font-size: 12px; word-break: break-all; }}
</style>
</head>
<body class="escuro">
<header>
  <h1>{NOME_DO_TEMA}</h1>
  <div class="controles">
    <label>Tamanho <input id="tam" type="range" min="32" max="160" step="16" value="96"> <span id="tamv">96</span>px</label>
    <button data-fundo="escuro" aria-pressed="true">Escuro</button>
    <button data-fundo="claro" aria-pressed="false">Claro</button>
    <button data-fundo="parede" aria-pressed="false">Papel de parede</button>
  </div>
</header>
{''.join(blocos)}
<script>
  const tam = document.getElementById('tam'), tamv = document.getElementById('tamv');
  tam.addEventListener('input', () => {{
    document.documentElement.style.setProperty('--tam', tam.value + 'px'); tamv.textContent = tam.value; }});
  document.querySelectorAll('[data-fundo]').forEach(b => b.addEventListener('click', () => {{
    document.body.className = b.dataset.fundo;
    document.querySelectorAll('[data-fundo]').forEach(x => x.setAttribute('aria-pressed', x === b));
  }}));
</script>
</body>
</html>
""")


# ── Main ──────────────────────────────────────────────────────────────────
def salvar_folha(itens, destino, tam=96, colunas=10):
    """Folha de contato em PNG (precisa de pycairo e librsvg via gi)."""
    import cairo
    import gi
    gi.require_version("Rsvg", "2.0")
    from gi.repository import Rsvg

    pad = 14
    linhas = (len(itens) + colunas - 1) // colunas
    sup = cairo.ImageSurface(cairo.FORMAT_ARGB32, colunas * (tam + pad) + pad, linhas * (tam + pad) + pad)
    ctx = cairo.Context(sup)
    grad = cairo.LinearGradient(0, 0, sup.get_width(), sup.get_height())
    grad.add_color_stop_rgb(0, 0.29, 0.41, 0.54)
    grad.add_color_stop_rgb(1, 0.07, 0.06, 0.11)
    ctx.set_source(grad)
    ctx.paint()
    for i, it in enumerate(itens):
        vp = Rsvg.Rectangle()
        vp.x, vp.y = pad + (i % colunas) * (tam + pad), pad + (i // colunas) * (tam + pad)
        vp.width = vp.height = tam
        Rsvg.Handle.new_from_data(it["svg"].encode()).render_document(ctx, vp)
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    sup.write_to_png(str(destino))


def main():
    corrigidos = corrigir_icones_absolutos()
    itens, problemas, escritos = gerar()
    if "--sem-cache" not in sys.argv:
        atualizar_cache()
    escrever_preview(itens, problemas)
    if "--folha" in sys.argv:
        salvar_folha(itens, sys.argv[sys.argv.index("--folha") + 1])

    automaticos = [it for it in itens if "Automáticos" in it["secoes"]]
    print(f"{len(escritos)} SVGs em {PASTA_SCALABLE}")
    print(f"Preview: {PREVIEW}")
    for nome in corrigidos:
        print(f"Icon= absoluto trocado por nome em {nome}")
    if automaticos:
        print("\nTiles automáticos:")
        for it in automaticos:
            print(f"  - {it['rotulo']} ({it['nomes'][0]}, {it['glifo']})")
    if problemas:
        print("\nSem mapeamento:")
        for rotulo, origem, onde, problema, _ in problemas:
            print(f"  - {rotulo}: {problema}  [{onde}]")


if __name__ == "__main__":
    main()
