#!/usr/bin/env python3
"""Gerador do tema GTK 3 / GTK 4 / libadwaita do Brisa.

    python3 gtk/gerar.py                 gera em build/themes/<nome> e o preview-gtk.html
    python3 gtk/gerar.py --destino DIR   gera noutra pasta (o instalador usa ~/.local/share/themes)

Os valores vêm de config.toml ([paleta] e [gtk]); o CSS mora em gtk/modelos/.
Não aplica nada: no fim, imprime os comandos para instalar e aplicar.
"""
import base64
import html
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
CONFIG = tomllib.loads((RAIZ / "config.toml").read_text())
NOME = CONFIG["tema"]["nome"]
PAL = CONFIG["paleta"]
GTK = CONFIG["gtk"]
MODELOS = AQUI / "modelos"


def _arg(nome, padrao=None):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


DESTINO = Path(_arg("--destino", RAIZ / "build/themes" / NOME)).expanduser().resolve()
PREVIEW = RAIZ / "preview-gtk.html"
SIMBOLICOS = RAIZ / "build" / NOME / "symbolic/ui"   # gerados pela Fase 1 (icons/gerar.py)


# ── Cores e contraste (WCAG 2) ────────────────────────────────────────────
def _rgb(hexa):
    hexa = hexa.lstrip("#")
    return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def misturar(a, b, t):
    return _hex(tuple(x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))))


def luminancia(hexa):
    def canal(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (canal(c) for c in _rgb(hexa))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def texto_sobre(fundo, minimo=4.5):
    """Texto para pôr sobre `fundo`: um tom bem escuro da própria cor se passar
    no AA (fica mais elegante que preto puro), senão branco ou preto."""
    for t in (0.78, 0.86, 0.93):
        escuro = misturar(fundo, "#000000", t)
        if contraste(escuro, fundo) >= minimo:
            return escuro
    return max(("#FFFFFF", "#000000"), key=lambda c: contraste(c, fundo))


def destaque_sobre(cor, fundo, minimo=4.5):
    """A cor usada como texto/ícone sobre o fundo escuro, clareada se preciso."""
    for t in (0, 0.15, 0.3, 0.45, 0.6):
        c = misturar(cor, "#FFFFFF", t)
        if contraste(c, fundo) >= minimo:
            return c
    return "#FFFFFF"


def cor_da_paleta(valor):
    return PAL.get(valor, valor)


def valores():
    sup = GTK["superficies"]
    bj = GTK["botoes_janela"]
    escurece = bj["borda_mais_escura"]
    accent = cor_da_paleta(GTK["accent"])
    v = {
        "ACCENT": accent,
        "ACCENT_TEXTO": texto_sobre(accent),
        "ACCENT_DESTAQUE": destaque_sobre(accent, sup["janela"]),
        "ACCENT_BORDA": misturar(accent, "#000000", escurece),
        "ACCENT_HOVER": misturar(accent, "#FFFFFF", 0.08),
        "ACCENT_ATIVO": misturar(accent, "#000000", 0.12),
        "JANELA": sup["janela"], "CONTEUDO": sup["conteudo"], "TEXTO": sup["texto"],
        "BARRA_TITULO": sup["barra_titulo"], "BARRA_TITULO_SEM_FOCO": sup["barra_titulo_sem_foco"],
        "BARRA_LATERAL": sup["barra_lateral"],
        "BARRA_LATERAL_SEM_FOCO": misturar(sup["barra_lateral"], sup["janela"], 0.5),
        "BARRA_LATERAL_SECUNDARIA": sup["barra_lateral_secundaria"],
        "DIALOGO": sup["dialogo"], "POPOVER": sup["popover"], "MINIATURA": sup["miniatura"],
        "RAIO_JANELA": GTK["raio_janela"],
        "TAM": bj["tamanho"], "ESPACO": bj["espaco"], "MEIO_ESPACO": bj["espaco"] / 2,
        # Círculo = glifo + 1px de respiro + 1px de borda de cada lado.
        "GLIFO": bj["glifo"], "GLIFO_TAM": bj["tamanho"] - 4, "IMAGEM_RESPIRO": 1,
        "GLIFO_ESCALA": round((bj["tamanho"] - 4) / 16, 3),
        "ESCURECER": "rgba(0, 0, 0, 0.18)",
        "SEM_FOCO": bj["sem_foco"], "SEM_FOCO_BORDA": misturar(bj["sem_foco"], "#000000", escurece),
        "FECHAR": PAL["coral"], "FECHAR_BORDA": misturar(PAL["coral"], "#000000", escurece),
        "MINIMIZAR": PAL["ambar"], "MINIMIZAR_BORDA": misturar(PAL["ambar"], "#000000", escurece),
        "MAXIMIZAR": PAL["menta"], "MAXIMIZAR_BORDA": misturar(PAL["menta"], "#000000", escurece),
    }
    for nome in ("coral", "ambar", "menta"):
        n = nome.upper()
        v[n] = PAL[nome]
        v[f"{n}_TEXTO"] = texto_sobre(PAL[nome])
        v[f"{n}_BORDA"] = misturar(PAL[nome], "#000000", escurece)
        v[f"{n}_DESTAQUE"] = destaque_sobre(PAL[nome], sup["janela"])
    return v


# ── Versões instaladas ────────────────────────────────────────────────────
def versao_rpm(pacote):
    try:
        return subprocess.run(["rpm", "-q", "--qf", "%{VERSION}", pacote],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "?"


def preencher(modelo, v):
    texto = (MODELOS / modelo).read_text()
    for k, val in v.items():
        texto = texto.replace("{{" + k + "}}", str(val))
    if "{{" in texto:
        raise SystemExit(f"{modelo}: marcador sem valor: {texto[texto.index('{{'):][:30]}")
    return texto


# ── Validação com o parser real do GTK ────────────────────────────────────
VALIDAR_GTK4 = r"""
import sys, gi
gi.require_version('Gtk', '4.0'); from gi.repository import Gtk
erros = []
for caminho in sys.argv[1:]:
    p = Gtk.CssProvider()
    p.connect('parsing-error', lambda _p, sec, err, c=caminho: erros.append(f'{c}:{sec.get_start_location().lines + 1}: {err.message}'))
    p.load_from_path(caminho)
print('\n'.join(erros))
"""
VALIDAR_GTK3 = r"""
import sys, gi
gi.require_version('Gtk', '3.0'); from gi.repository import Gtk
for caminho in sys.argv[1:]:
    try:
        Gtk.CssProvider().load_from_path(caminho)
    except Exception as e:
        print(f'{caminho}: {e}')
"""


def validar(arquivos4, arquivos3):
    saida = []
    for codigo, arquivos in ((VALIDAR_GTK4, arquivos4), (VALIDAR_GTK3, arquivos3)):
        r = subprocess.run([sys.executable, "-c", codigo, *map(str, arquivos)], capture_output=True, text=True)
        saida += [l for l in (r.stdout + r.stderr).splitlines() if l.strip() and "Warning" not in l]
    return saida


# ── Preview ───────────────────────────────────────────────────────────────
def preview(v, avisos, versoes):
    def mascara(nome):
        # Embutido como data URI: navegadores bloqueiam máscara de outro arquivo em file://.
        alvo = SIMBOLICOS / f"{nome}.svg"
        if not alvo.exists():
            return ""
        url = "data:image/svg+xml;base64," + base64.b64encode(alvo.read_bytes()).decode()
        return f"-webkit-mask-image:url({url});mask-image:url({url})"

    def janela(titulo, foco=True, hover=False, maximizada=False):
        classes = " ".join(c for c, on in (("sem-foco", not foco), ("hover", hover), ("max", maximizada)) if on)
        botoes = "".join(
            f'<span class="bt {nome}"><i style="{mascara(icone)}"></i></span>'
            for nome, icone in (("fechar", "window-close-symbolic"), ("minimizar", "window-minimize-symbolic"),
                                ("maximizar", "window-restore-symbolic" if maximizada else "window-maximize-symbolic")))
        return f"""
<figure class="janela {classes}">
  <div class="barra"><div class="botoes">{botoes}</div><b>Arquivos</b></div>
  <div class="corpo">
    <aside><p class="sel">Pasta pessoal</p><p>Documentos</p><p>Downloads</p><p>Imagens</p></aside>
    <main>
      <div class="linha"><button class="sug">Salvar</button><button>Cancelar</button><button class="dest">Excluir</button></div>
      <div class="linha"><span class="switch on"><i></i></span><span class="check on"></span><span>Opção marcada</span></div>
      <div class="linha"><span class="entry">Pesquisar…</span></div>
      <div class="linha"><span class="progresso"><i></i></span></div>
      <p class="link">Um link no destaque</p>
    </main>
  </div>
  <figcaption>{titulo}</figcaption>
</figure>"""

    contrastes = [
        ("Texto no destaque", v["ACCENT_TEXTO"], v["ACCENT"]),
        ("Destaque sobre a janela", v["ACCENT_DESTAQUE"], v["JANELA"]),
        ("Texto na janela", v["TEXTO"], v["JANELA"]),
        ("Texto no botão de excluir", v["CORAL_TEXTO"], v["CORAL"]),
    ]
    linhas = "".join(
        f'<tr><td>{n}</td><td><span class="am" style="background:{bg};color:{fg}">Aa</span></td>'
        f'<td>{contraste(fg, bg):.1f}:1 {"✓ AA" if contraste(fg, bg) >= 4.5 else "✗"}</td></tr>'
        for n, fg, bg in contrastes)
    lista_avisos = ("".join(f"<li><code>{html.escape(a)}</code></li>" for a in avisos)
                    or "<li>Nenhum erro: o GTK 4 e o GTK 3 instalados aceitaram todo o CSS.</li>")

    PREVIEW.write_text(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NOME} GTK preview</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px 16px 64px; background: radial-gradient(120% 90% at 20% 0%, #3b4f66, #15161c 60%) fixed;
         color: #e8e8ec; font: 14px/1.4 "Adwaita Sans", Cantarell, system-ui, sans-serif; }}
  header, section {{ max-width: 1300px; margin: 0 auto 28px; }}
  h1 {{ margin: 0 0 4px; font-size: 22px; }} h2 {{ font-size: 15px; margin: 0 0 12px; }}
  .sutil {{ color: #9a9aa6; font-size: 13px; }}
  .janelas {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(560px, 1fr)); gap: 24px; }}
  @media (max-width: 640px) {{ .janelas {{ grid-template-columns: 1fr; }} }}
  .janela {{ margin: 0; border-radius: {v["RAIO_JANELA"]}px; overflow: hidden; background: {v["JANELA"]}; color: {v["TEXTO"]};
            box-shadow: 0 18px 50px rgba(0,0,0,.5), 0 0 0 1px rgba(255,255,255,.07); position: relative; }}
  .janela.max {{ border-radius: 0; }}
  .barra {{ height: 46px; background: {v["BARRA_TITULO"]}; display: flex; align-items: center; justify-content: center; position: relative;
           border-bottom: 1px solid rgba(0,0,0,.36); }}
  .sem-foco .barra {{ background: {v["BARRA_TITULO_SEM_FOCO"]}; }} .sem-foco .barra b {{ opacity: .5; }}
  .botoes {{ position: absolute; left: 14px; display: flex; gap: {v["ESPACO"]}px; }}
  .bt {{ width: {v["TAM"]}px; height: {v["TAM"]}px; border-radius: 50%; border: 1px solid; display: grid; place-items: center; }}
  .bt i {{ width: {v["GLIFO_TAM"]}px; height: {v["GLIFO_TAM"]}px; background: transparent; mask-size: contain; -webkit-mask-size: contain; }}
  .hover .bt i {{ background: {v["GLIFO"]}; }}
  .fechar {{ background: {v["FECHAR"]}; border-color: {v["FECHAR_BORDA"]}; }}
  .minimizar {{ background: {v["MINIMIZAR"]}; border-color: {v["MINIMIZAR_BORDA"]}; }}
  .maximizar {{ background: {v["MAXIMIZAR"]}; border-color: {v["MAXIMIZAR_BORDA"]}; }}
  .sem-foco:not(.hover) .bt {{ background: {v["SEM_FOCO"]}; border-color: {v["SEM_FOCO_BORDA"]}; }}
  .corpo {{ display: grid; grid-template-columns: 170px 1fr; min-height: 230px; }}
  aside {{ background: {v["BARRA_LATERAL"]}; padding: 8px; }} .sem-foco aside {{ background: {v["BARRA_LATERAL_SEM_FOCO"]}; }}
  aside p {{ margin: 2px 0; padding: 6px 10px; border-radius: 8px; font-size: 13px; }}
  aside .sel {{ background: {v["ACCENT"]}; color: {v["ACCENT_TEXTO"]}; font-weight: 600; }}
  main {{ background: {v["CONTEUDO"]}; padding: 14px; display: flex; flex-direction: column; gap: 12px; }}
  .linha {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; font-size: 13px; }}
  button {{ font: inherit; font-size: 13px; font-weight: 600; border: 0; border-radius: 8px; padding: 6px 14px;
           background: rgba(255,255,255,.1); color: {v["TEXTO"]}; }}
  button.sug {{ background: {v["ACCENT"]}; color: {v["ACCENT_TEXTO"]}; }}
  button.dest {{ background: {v["CORAL"]}; color: {v["CORAL_TEXTO"]}; }}
  .switch {{ width: 42px; height: 24px; border-radius: 12px; background: rgba(255,255,255,.15); position: relative; }}
  .switch.on {{ background: {v["ACCENT"]}; }} .switch i {{ position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: #fff; }}
  .switch.on i {{ left: 21px; }}
  .check {{ width: 18px; height: 18px; border-radius: 5px; background: {v["ACCENT"]}; position: relative; }}
  .check::after {{ content: ""; position: absolute; left: 6px; top: 2px; width: 4px; height: 9px; border: solid {v["ACCENT_TEXTO"]};
                  border-width: 0 2px 2px 0; transform: rotate(45deg); }}
  .entry {{ flex: 1; padding: 6px 10px; border-radius: 8px; background: rgba(255,255,255,.08); box-shadow: 0 0 0 2px {v["ACCENT"]};
           color: #9a9aa6; }}
  .progresso {{ flex: 1; height: 6px; border-radius: 3px; background: rgba(255,255,255,.12); }}
  .progresso i {{ display: block; width: 62%; height: 100%; border-radius: 3px; background: {v["ACCENT"]}; }}
  .link {{ margin: 0; color: {v["ACCENT_DESTAQUE"]}; text-decoration: underline; font-size: 13px; }}
  figcaption {{ position: absolute; right: 12px; top: 13px; font-size: 11px; color: #8a8a93; }}
  table {{ border-collapse: collapse; background: #151517; border-radius: 12px; overflow: hidden; }}
  td {{ padding: 6px 12px; border-bottom: 1px solid #26262a; font-size: 13px; }}
  .am {{ display: inline-block; padding: 2px 10px; border-radius: 6px; font-weight: 700; }}
  ul {{ background: #151517; border-radius: 12px; padding: 12px 12px 12px 30px; margin: 0; font-size: 13px; }}
  code {{ color: #c8c8d0; }}
</style></head><body>
<header><h1>{NOME} · Fase 2 <span class="sutil">botões de janela e GTK</span></h1>
<p class="sutil">Versões detectadas: {html.escape(" · ".join(versoes))}. Mock em HTML com as cores do config.toml
(destaque {GTK["accent"]} = {v["ACCENT"]}); os glifos dos botões são os simbólicos da Fase 1.</p></header>
<section><h2>Janelas</h2><div class="janelas">
{janela("Em foco")}{janela("Mouse sobre os botões", hover=True)}{janela("Sem foco", foco=False)}
{janela("Sem foco, mouse sobre os botões", foco=False, hover=True)}{janela("Maximizada: glifo de restaurar", hover=True, maximizada=True)}
</div></section>
<section><h2>Contraste</h2><table>{linhas}</table></section>
<section><h2>Validação do CSS</h2><ul>{lista_avisos}</ul></section>
</body></html>
""")


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    v = valores()
    versoes = {"gtk4": versao_rpm("gtk4"), "gtk3": versao_rpm("gtk3"), "adw": versao_rpm("libadwaita")}
    v.update({"VERSAO_GTK4": versoes["gtk4"], "VERSAO_GTK3": versoes["gtk3"], "VERSAO_ADW": versoes["adw"]})
    v["BOTOES"] = preencher("botoes-gtk4.css", v)

    arquivos = {
        "gtk-3.0/gtk.css": preencher("gtk3.css", v),
        "gtk-4.0/gtk.css": preencher("gtk4.css", v),
        "gtk-4.0/libadwaita.css": preencher("libadwaita.css", v),
    }
    for rel, texto in arquivos.items():
        (DESTINO / rel).parent.mkdir(parents=True, exist_ok=True)
        (DESTINO / rel).write_text(texto)
    (DESTINO / "index.theme").write_text(
        f"[Desktop Entry]\nType=X-GNOME-Metatheme\nName={NOME}\n"
        "Comment=Tema escuro grafite com destaque configurável\nEncoding=UTF-8\n\n"
        f"[X-GNOME-Metatheme]\nGtkTheme={NOME}\nIconTheme={NOME}\nButtonLayout=close,minimize,maximize:\n")
    (DESTINO / "gtk-4.0/cores.json").write_text(json.dumps(v | {"BOTOES": "…"}, ensure_ascii=False, indent=1))

    avisos = validar([DESTINO / "gtk-4.0/gtk.css", DESTINO / "gtk-4.0/libadwaita.css"], [DESTINO / "gtk-3.0/gtk.css"])
    nomes = [f"GNOME Shell {subprocess.run(['gnome-shell', '--version'], capture_output=True, text=True).stdout.split()[-1]}",
             f"libadwaita {versoes['adw']}", f"GTK {versoes['gtk4']}", f"GTK {versoes['gtk3']}"]
    preview(v, avisos, nomes)

    print(f"Tema GTK em {DESTINO}")
    print(f"Preview: {PREVIEW}")
    print(f"Destaque {v['ACCENT']} com texto {v['ACCENT_TEXTO']} "
          f"(contraste {contraste(v['ACCENT_TEXTO'], v['ACCENT']):.1f}:1)")
    print("Validação: " + ("sem erros" if not avisos else f"{len(avisos)} aviso(s)"))
    for a in avisos:
        print("  - " + a)


if __name__ == "__main__":
    main()
