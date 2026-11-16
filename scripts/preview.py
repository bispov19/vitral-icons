#!/usr/bin/env python3
"""Gera tudo numa pasta de build (sem tocar no sistema) e monta o preview.html
com as três partes do tema e o relatório final.

    python3 scripts/preview.py            regenera ícones, GTK e Shell em build/ e o preview
    python3 scripts/preview.py --rapido   só monta o preview com o que já está em build/
    python3 scripts/preview.py --folha    também atualiza docs/preview.png (imagem do README)

Saídas: preview.html (abas: Ícones, Janelas e GTK, GNOME Shell, Relatório) e
build/relatorio.md.
"""
import html
import json
import subprocess
import sys
import tomllib
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = tomllib.loads((RAIZ / "config.toml").read_text())
NOME = CONFIG["tema"]["nome"]
BUILD = RAIZ / "build"

PENDENCIAS = [
    "GTK 3 não repassa o hover do grupo de botões para os vizinhos: lá o glifo aparece botão a botão "
    "(no GTK 4/libadwaita aparece no grupo todo, como pedido).",
    "O GNOME Shell não desfoca o fundo sem extensão (o St não tem backdrop-filter): o vidro dos menus, "
    "do painel e das notificações é translúcido, sem blur.",
    "LibreOffice Draw, Math e Base estão mapeados pelo nome do ícone, mas não têm .desktop instalado "
    "(só aparecem se você instalar esses módulos).",
    "A data do ícone do Calendário no tema é atualizada pelo timer do systemd à meia-noite; a dock (orla-dock) "
    "desenha a própria data, ou segue o tema, conforme a opção dela.",
    "Web apps do Brave/Chrome: o Icon= com caminho absoluto só é trocado pelo nome quando os ícones são "
    "instalados no sistema (install.sh), nunca num build de teste.",
    "Apps Flatpak só leem o CSS do tema com o apply.sh --flatpak (que faz o flatpak override).",
    "O CSS do Shell é derivado do tema do GNOME Shell (GPL-2.0-or-later): é gerado na sua máquina a partir "
    "do Shell instalado e não fica no repositório.",
    "Fase 5 (cursores claro e escuro) ainda não feita: é opcional e precisa do xcursorgen, que não está "
    "instalado (sudo dnf install xcursorgen).",
]


def gerar():
    for cmd in (["python3", "icons/gerar.py", "--destino", f"build/{NOME}"],
                ["python3", "gtk/gerar.py"], ["python3", "shell/gerar.py"]):
        print("==> " + " ".join(cmd))
        subprocess.run(cmd, cwd=RAIZ, check=True, stdout=subprocess.DEVNULL)


def tipo(fonte):
    return "desenho próprio" if fonte.startswith("desenho") else "Simple Icons" if fonte.startswith("Simple") \
        else "original do app"


def relatorio():
    dados = json.loads((BUILD / NOME / "relatorio.json").read_text())
    icones = dados["icones"]
    cont = Counter(tipo(i["fonte"]) for i in icones)
    versoes = [subprocess.run(["gnome-shell", "--version"], capture_output=True, text=True).stdout.strip()]
    versoes += subprocess.run(["rpm", "-q", "--qf", "%{NAME} %{VERSION}\\n", "libadwaita", "gtk4", "gtk3"],
                              capture_output=True, text=True).stdout.split("\n")
    md = [f"# Relatório do tema {NOME}", "",
          "Versões detectadas: " + " · ".join(v for v in versoes if v), "",
          f"## Fonte de cada ícone ({len(icones)} no total)", "",
          f"- original do app: {cont['original do app']}",
          f"- Simple Icons: {cont['Simple Icons']}",
          f"- desenho próprio: {cont['desenho próprio']}", "",
          "| Ícone | Nomes | Fonte |", "| --- | --- | --- |"]
    for i in icones:
        md.append(f"| {i['rotulo']} | `{', '.join(i['nomes'])}` | {i['fonte']} |")
    auto = [i for i in icones if "automático" in i["fonte"]]
    md += ["", "## Apps sem mapeamento manual", ""]
    md += [f"- {i['rotulo']}: tile automático com o ícone original ({i['fonte']})" for i in auto] or \
          ["- Nenhum: todos os apps visíveis têm fonte definida em icons/glifos.py. "
           "Apps instalados no futuro entram sozinhos com o ícone original no tile."]
    if dados["problemas"]:
        md += ["", "Avisos do gerador:", ""] + [f"- {p['rotulo']}: {p['problema']}" for p in dados["problemas"]]
    md += ["", "## Pendências e limitações", ""] + [f"- {p}" for p in PENDENCIAS]
    texto = "\n".join(md) + "\n"
    (BUILD / "relatorio.md").write_text(texto)
    return texto, cont, len(icones)


def md_para_html(texto):
    """Conversor mínimo (títulos, listas, tabela) só para o relatório."""
    saida, tabela = [], False
    for linha in texto.splitlines():
        if linha.startswith("| ---"):
            continue
        if linha.startswith("|"):
            celulas = [html.escape(c.strip()).replace("`", "") for c in linha.strip("|").split("|")]
            if not tabela:
                saida.append("<table><tr>" + "".join(f"<th>{c}</th>" for c in celulas) + "</tr>")
                tabela = True
            else:
                saida.append("<tr>" + "".join(f"<td>{c}</td>" for c in celulas) + "</tr>")
            continue
        if tabela:
            saida.append("</table>")
            tabela = False
        if linha.startswith("## "):
            saida.append(f"<h2>{html.escape(linha[3:])}</h2>")
        elif linha.startswith("# "):
            continue
        elif linha.startswith("- "):
            saida.append(f"<li>{html.escape(linha[2:])}</li>")
        elif linha.strip():
            saida.append(f"<p>{html.escape(linha)}</p>")
    return "\n".join(saida)


def folha(destino, tam=96, colunas=10, pad=14):
    """Folha de contato com apps, pastas e tipos de arquivo, para o README."""
    import cairo
    import gi
    gi.require_version("Rsvg", "2.0")
    from gi.repository import Rsvg
    dados = json.loads((BUILD / NOME / "relatorio.json").read_text())
    caminhos = {}
    for ctx in ("apps", "places", "devices", "mimetypes"):
        for f in (BUILD / NOME / "scalable" / ctx).glob("*.svg"):
            caminhos.setdefault(f.stem, f)
    itens = [caminhos[i["nomes"][0]] for i in dados["icones"] if i["nomes"][0] in caminhos]
    linhas = (len(itens) + colunas - 1) // colunas
    sup = cairo.ImageSurface(cairo.FORMAT_ARGB32, colunas * (tam + pad) + pad, linhas * (tam + pad) + pad)
    ctx = cairo.Context(sup)
    ctx.set_source_rgb(0.04, 0.04, 0.05)
    ctx.paint()
    for n, arq in enumerate(itens):
        vp = Rsvg.Rectangle()
        vp.x, vp.y = pad + (n % colunas) * (tam + pad), pad + (n // colunas) * (tam + pad)
        vp.width = vp.height = tam
        Rsvg.Handle.new_from_file(str(arq)).render_document(ctx, vp)
    destino.parent.mkdir(parents=True, exist_ok=True)
    sup.write_to_png(str(destino))


def main():
    if "--rapido" not in sys.argv:
        gerar()
    if "--folha" in sys.argv:
        folha(RAIZ / "docs/preview.png")
        print(f"Imagem do README: {RAIZ / 'docs/preview.png'}")
    texto, cont, total = relatorio()
    abas = [("icones", "Ícones", "preview-icones.html"), ("gtk", "Janelas e GTK", "preview-gtk.html"),
            ("shell", "GNOME Shell", "preview-shell.html")]
    botoes = "".join(f'<button data-aba="{i}"{" aria-pressed=true" if n == 0 else ""}>{t}</button>'
                     for n, (i, t, _) in enumerate(abas)) + '<button data-aba="relatorio">Relatório</button>'
    quadros = "".join(f'<iframe id="{i}" src="{arq}" title="{t}"{"" if n == 0 else " hidden"}></iframe>'
                      for n, (i, t, arq) in enumerate(abas))
    (RAIZ / "preview.html").write_text(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NOME} preview</title>
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; height: 100%; background: #0b0b0d; color: #e8e8ec;
               font: 14px/1.45 "Adwaita Sans", Cantarell, system-ui, sans-serif; }}
  header {{ display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; padding: 12px 16px;
           border-bottom: 1px solid #222226; }}
  h1 {{ margin: 0; font-size: 18px; }} h1 small {{ color: #8a8a93; font-weight: 400; font-size: 13px; }}
  nav {{ display: flex; gap: 6px; flex-wrap: wrap; }}
  nav button {{ font: inherit; color: #e8e8ec; background: #1b1b1e; border: 1px solid #2c2c31; border-radius: 999px;
               padding: 5px 14px; cursor: pointer; }}
  nav button[aria-pressed=true] {{ background: #4FC7A2; color: #112C24; border-color: #4FC7A2; font-weight: 600; }}
  iframe {{ border: 0; width: 100%; height: calc(100% - 58px); display: block; }}
  #relatorio {{ max-width: 1100px; margin: 0 auto; padding: 16px; overflow: auto; height: calc(100% - 58px); }}
  #relatorio table {{ border-collapse: collapse; width: 100%; font-size: 12.5px; background: #151517; border-radius: 10px; }}
  #relatorio th, #relatorio td {{ text-align: left; padding: 4px 10px; border-bottom: 1px solid #26262a; }}
  #relatorio h2 {{ font-size: 15px; margin-top: 22px; }} #relatorio li {{ margin: 3px 0; }}
</style></head><body>
<header><h1>{NOME} <small>{total} ícones · {cont['original do app']} originais · {cont['Simple Icons']} Simple Icons ·
  {cont['desenho próprio']} desenhos próprios</small></h1><nav>{botoes}</nav></header>
{quadros}
<section id="relatorio" hidden>{md_para_html(texto)}</section>
<script>
  const botoes = document.querySelectorAll('nav button');
  botoes.forEach(b => b.addEventListener('click', () => {{
    botoes.forEach(x => x.setAttribute('aria-pressed', x === b));
    document.querySelectorAll('iframe, #relatorio').forEach(el => el.hidden = el.id !== b.dataset.aba);
  }}));
</script>
</body></html>
""")
    print(f"Preview: {RAIZ / 'preview.html'}")
    print(f"Relatório: {BUILD / 'relatorio.md'}")


if __name__ == "__main__":
    main()
