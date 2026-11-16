#!/usr/bin/env python3
"""Gerador do tema do GNOME Shell do Brisa (carregado pela extensão User Themes).

    python3 shell/gerar.py                 gera em build/themes/<nome>/gnome-shell e o preview-shell.html
    python3 shell/gerar.py --destino DIR   gera noutra pasta de tema (o instalador usa ~/.local/share/themes/<nome>)

Parte do CSS padrão do Shell INSTALADO (extraído do gnome-shell-theme.gresource
na hora de gerar, então acompanha a versão do GNOME), troca a cor de destaque e
acrescenta só as sobrescritas de shell/modelos/brisa.css. Não aplica nada.
"""
import html
import importlib.util
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
CONFIG = tomllib.loads((RAIZ / "config.toml").read_text())
NOME = CONFIG["tema"]["nome"]
PAL = CONFIG["paleta"]
SH = CONFIG["shell"]
GRESOURCE = Path("/usr/share/gnome-shell/gnome-shell-theme.gresource")
EXTENSAO = "user-theme@gnome-shell-extensions.gcampax.github.com"
# Extensões de dock conhecidas: se uma estiver ativa, o dash fica intocado.
DOCKS = ("orla-dock", "dash-to-dock", "dash-to-panel", "ubuntu-dock", "luma-dock")


def _arg(nome, padrao=None):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


DESTINO = Path(_arg("--destino", RAIZ / "build/themes" / NOME)).expanduser().resolve()
PREVIEW = RAIZ / "preview-shell.html"
ICONES = RAIZ / "build" / NOME   # ícones gerados na Fase 1, usados no mock do Alt+Tab

# Funções de cor e contraste compartilhadas com o gerador do GTK.
_spec = importlib.util.spec_from_file_location("gtk_gerar", RAIZ / "gtk/gerar.py")
cores = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cores)


def rodar(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


def rgba(hexa, opacidade):
    r, g, b = cores._rgb(hexa)
    return f"rgba({r}, {g}, {b}, {opacidade})"


def css_padrao():
    """O CSS escuro do Shell instalado (ou o único, em versões antigas)."""
    lista = rodar("gresource", "list", str(GRESOURCE)).splitlines()
    for nome in ("/org/gnome/shell/theme/gnome-shell-dark.css", "/org/gnome/shell/theme/gnome-shell.css"):
        if nome in lista:
            return nome, rodar("gresource", "extract", str(GRESOURCE), nome)
    raise SystemExit(f"Nenhum CSS do Shell encontrado em {GRESOURCE}")


def valores(versao):
    accent = cores.cor_da_paleta(SH["accent"])
    return {
        "VERSAO": versao,
        "ACCENT": accent, "ACCENT_TEXTO": cores.texto_sobre(accent),
        "AMBAR": PAL["ambar"], "AMBAR_TEXTO": cores.texto_sobre(PAL["ambar"]),
        "TEXTO": CONFIG["gtk"]["superficies"]["texto"],
        "PAINEL": rgba(SH["painel_cor"], SH["painel_opacidade"]),
        "VIDRO": rgba(SH["vidro_cor"], SH["vidro_opacidade"]),
        "VIDRO_SOLIDO": SH["vidro_cor"],
        "VIDRO_BORDA": f"rgba(255, 255, 255, {SH['vidro_borda_opacidade']})",
        "RAIO": SH["raio"], "RAIO_ITENS": SH["raio_itens"],
    }


def conferir(base, extra):
    """Erros de digitação e propriedades que o St não conhece: toda classe, id
    e propriedade usada nas sobrescritas precisa existir no tema original."""
    avisos = []
    if base.count("{") != base.count("}") or extra.count("{") != extra.count("}"):
        avisos.append("chaves desbalanceadas")
    sem_comentarios = re.sub(r"/\*.*?\*/", "", extra, flags=re.S)
    seletores = set(re.findall(r"[.#][a-zA-Z][\w-]*", re.sub(r"\{[^}]*\}", "{}", sem_comentarios)))
    for s in sorted(seletores):
        if not re.search(re.escape(s) + r"(?![\w-])", base):
            avisos.append(f"seletor {s} não existe no tema do Shell instalado")
    props = set(re.findall(r"([a-z-]+)\s*:", "".join(re.findall(r"\{([^}]*)\}", sem_comentarios))))
    for p in sorted(props):
        if not re.search(r"(?<![\w-])" + re.escape(p) + r"\s*:", base):
            avisos.append(f"propriedade {p} não é usada pelo tema do Shell instalado")
    return avisos


def dock_ativa():
    ativas = rodar("gsettings", "get", "org.gnome.shell", "enabled-extensions")
    return [d for d in DOCKS if d in ativas]


# ── Preview ───────────────────────────────────────────────────────────────
def preview(v, avisos, versao, docks):
    def icone(nome, ctx="apps"):
        alvo = ICONES / "scalable" / ctx / f"{nome}.svg"
        return html.escape(os.path.relpath(alvo, PREVIEW.parent)) if alvo.exists() else ""

    def toggle(rotulo, sub, ligado):
        return (f'<div class="toggle{" on" if ligado else ""}"><b>{rotulo}</b><span>{sub}</span></div>')

    dias = "".join(f'<span class="{"hoje" if d == 16 else ""}">{d}</span>' for d in range(1, 31))
    alt_tab = "".join(f'<div class="item{" sel" if i == 1 else ""}"><img src="{icone(n)}" alt=""></div>'
                      for i, n in enumerate(("org.gnome.Nautilus", "firefox", "vscode", "spotify", "org.gnome.Ptyxis")))
    lista_avisos = ("".join(f"<li>{html.escape(a)}</li>" for a in avisos)
                    or "<li>Sem avisos: todo seletor e propriedade das sobrescritas existe no tema do Shell instalado.</li>")

    PREVIEW.write_text(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NOME} Shell preview</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; color: #f2f2f5; font: 14px/1.4 "Adwaita Sans", Cantarell, system-ui, sans-serif; background: #111; }}
  .tela {{ position: relative; height: 760px; overflow: hidden;
           background: radial-gradient(80% 70% at 25% 30%, #4d6f8f, transparent 70%),
                       radial-gradient(70% 60% at 80% 80%, #7a4f6e, transparent 70%), linear-gradient(160deg, #22344a, #191422); }}
  .painel {{ height: 32px; background: {v["PAINEL"]}; box-shadow: inset 0 -1px 0 rgba(255,255,255,.06);
            display: flex; align-items: center; justify-content: space-between; padding: 0 6px; font-weight: 600; font-size: 13px; }}
  .pb {{ padding: 3px 12px; border-radius: 8px; }} .pb.ativo {{ background: rgba(255,255,255,.2); }}
  .pb.hover {{ background: rgba(255,255,255,.12); }}
  .vidro {{ position: absolute; background: {v["VIDRO"]}; border: 1px solid {v["VIDRO_BORDA"]}; border-radius: {v["RAIO"]}px;
           box-shadow: 0 10px 30px rgba(0,0,0,.45); backdrop-filter: none; }}
  .rapido {{ right: 8px; top: 40px; width: 360px; padding: 14px; }}
  .grade {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }}
  .toggle {{ border-radius: {v["RAIO_ITENS"]}px; padding: 10px 14px; background: rgba(255,255,255,.1); display: flex; flex-direction: column; }}
  .toggle b {{ font-size: 13px; }} .toggle span {{ font-size: 11px; opacity: .7; }}
  .toggle.on {{ background: {v["ACCENT"]}; color: {v["ACCENT_TEXTO"]}; }}
  .slider {{ height: 6px; border-radius: 3px; background: rgba(255,255,255,.15); margin: 14px 4px; position: relative; }}
  .slider i {{ position: absolute; inset: 0 40% 0 0; background: {v["ACCENT"]}; border-radius: 3px; }}
  .slider i::after {{ content: ""; position: absolute; right: -9px; top: -6px; width: 18px; height: 18px; border-radius: 50%; background: #fff; }}
  .calendario {{ left: 22%; top: 40px; width: 560px; padding: 12px; display: grid;
                grid-template-columns: 1fr 230px; gap: 12px; }}
  .msgs {{ display: flex; flex-direction: column; gap: 8px; }}
  .msg {{ background: rgba(255,255,255,.08); border-radius: {v["RAIO_ITENS"]}px; padding: 10px 12px; font-size: 12.5px; }}
  .msg b {{ display: block; font-size: 13px; }}
  .cal {{ background: rgba(255,255,255,.06); border-radius: {v["RAIO_ITENS"]}px; padding: 10px; }}
  .cal h4 {{ margin: 0 0 8px; text-align: center; font-size: 13px; }}
  .dias {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; text-align: center; font-size: 12px; }}
  .dias span {{ padding: 4px 0; border-radius: 999px; }} .dias .hoje {{ background: {v["AMBAR"]}; color: {v["AMBAR_TEXTO"]}; font-weight: 700; }}
  .banner {{ left: 50%; transform: translateX(-50%); top: 470px; width: 420px; padding: 12px 14px; display: flex; gap: 12px; align-items: center; }}
  .banner img {{ width: 40px; height: 40px; }} .banner b {{ display: block; }}
  .osd {{ left: 60px; top: 560px; padding: 14px 18px; display: flex; gap: 14px; align-items: center; width: 280px; }}
  .osd .barra {{ flex: 1; height: 6px; border-radius: 3px; background: rgba(255,255,255,.15); position: relative; }}
  .osd .barra i {{ position: absolute; inset: 0 30% 0 0; background: {v["ACCENT"]}; border-radius: 3px; }}
  .alttab {{ right: 60px; top: 560px; padding: 12px; display: flex; gap: 8px; }}
  .alttab .item {{ width: 96px; height: 96px; border-radius: {v["RAIO_ITENS"]}px; display: grid; place-items: center; }}
  .alttab .item.sel {{ background: rgba(255,255,255,.12); box-shadow: inset 0 0 0 2px rgba(255,255,255,.35); }}
  .alttab img {{ width: 80px; height: 80px; }}
  section {{ max-width: 1100px; margin: 24px auto; padding: 0 16px; }}
  h1 {{ font-size: 20px; margin: 0 0 6px; }} .sutil {{ color: #9a9aa6; font-size: 13px; }}
  ul {{ background: #1b1b1e; border-radius: 12px; padding: 12px 12px 12px 30px; font-size: 13px; }}
</style></head><body>
<section><h1>{NOME} · Fase 3 <span class="sutil">tema do GNOME Shell</span></h1>
<p class="sutil">Base: CSS padrão do GNOME Shell {html.escape(versao)} instalado, destaque {SH["accent"]} = {v["ACCENT"]}.
Dash intocado{(" (dock ativa: " + ", ".join(docks) + ")") if docks else ""}. Mock em HTML: o Shell não aplica desfoque
sozinho (isso viria de uma extensão), então o vidro é translúcido sem blur, como aqui.</p></section>
<div class="tela">
  <div class="painel"><span class="pb ativo">Atividades</span><span class="pb hover">seg 16 nov  11:20</span>
    <span class="pb">⌁  ◉  ▮</span></div>
  <div class="vidro calendario">
    <div class="msgs"><div class="msg"><b>Thunderbird</b>3 mensagens novas</div>
      <div class="msg"><b>Spotify</b>Tocando agora: Brisa</div><div class="msg"><b>Atualizações</b>Tudo em dia</div></div>
    <div class="cal"><h4>Novembro de 2026</h4><div class="dias">{dias}</div></div>
  </div>
  <div class="vidro rapido">
    <div class="slider"><i></i></div><div class="slider"><i style="right:20%"></i></div>
    <div class="grade">{toggle("Wi-Fi", "Casa", True)}{toggle("Bluetooth", "Desligado", False)}
      {toggle("Estilo escuro", "", True)}{toggle("Modo de energia", "Equilibrado", False)}</div>
  </div>
  <div class="vidro banner"><img src="{icone("thunderbird")}" alt=""><div><b>Nova mensagem</b>Reunião às 15h</div></div>
  <div class="vidro osd"><span>🔊</span><div class="barra"><i></i></div></div>
  <div class="vidro alttab">{alt_tab}</div>
</div>
<section><h2 style="font-size:15px">Conferência do CSS</h2><ul>{lista_avisos}</ul></section>
</body></html>
""")


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    versao = rodar("gnome-shell", "--version").split()[-1]
    origem, base = css_padrao()
    v = valores(versao)
    # Destaque: o Shell usa -st-accent-color (vem do gsettings accent-color);
    # o Brisa fixa a cor do config.
    base_brisa = base.replace("-st-accent-fg-color", v["ACCENT_TEXTO"]).replace("-st-accent-color", v["ACCENT"])
    extra = (AQUI / "modelos/brisa.css").read_text()
    for k, val in v.items():
        extra = extra.replace("{{" + k + "}}", str(val))
    if "{{" in extra:
        raise SystemExit("brisa.css: marcador sem valor")
    avisos = conferir(base, extra)

    cabecalho = (f"/* Tema {NOME} para o GNOME Shell {versao}.\n"
                 f"   Gerado por shell/gerar.py a partir de {origem} (gnome-shell-theme.gresource)\n"
                 "   e de shell/modelos/brisa.css. Não edite aqui: regere. */\n\n")
    saida = DESTINO / "gnome-shell/gnome-shell.css"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(cabecalho + base_brisa + "\n" + extra)

    docks = dock_ativa()
    preview(v, avisos, versao, docks)
    print(f"Tema do Shell em {saida} ({saida.stat().st_size // 1024} KB, base {origem})")
    print(f"Preview: {PREVIEW}")
    print("Dash: intocado" + (f" (dock ativa: {', '.join(docks)})" if docks else ""))
    print("Conferência: " + ("sem avisos" if not avisos else f"{len(avisos)} aviso(s)"))
    for a in avisos:
        print("  - " + a)


if __name__ == "__main__":
    main()
