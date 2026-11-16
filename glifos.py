"""Glifos do tema Brisa e o mapa de apps.

Cada glifo é desenhado num quadro 128x128, centrado em (64,64), ocupando
mais ou menos x/y 30..98 (~60% do tile de 112px). O template (tile.svg)
já aplica stroke="currentColor", largura 6, pontas e cantos redondos;
aqui só entram as formas. Para partes cheias use D() ou fill="currentColor".
"""
from math import cos, sin, radians

# ── Paleta ────────────────────────────────────────────────────────────────
BRANCO = "#F2F2F5"
CORAL = "#F0685A"
AMBAR = "#F5B53F"
MENTA = "#4FC7A2"


# ── Primitivas ────────────────────────────────────────────────────────────
def _n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def P(d, extra=""):
    return f'<path d="{d}"{extra}/>'


def C(cx, cy, r):
    return f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}"/>'


def D(cx, cy, r):
    """Ponto cheio."""
    return f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="currentColor" stroke="none"/>'


def R(x, y, w, h, rx=0):
    return f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="{_n(rx)}"/>'


def E(cx, cy, rx, ry):
    return f'<ellipse cx="{_n(cx)}" cy="{_n(cy)}" rx="{_n(rx)}" ry="{_n(ry)}"/>'


def ponto(cx, cy, r, ang):
    a = radians(ang)
    return cx + r * cos(a), cy + r * sin(a)


def raios(cx, cy, r0, comprimentos, desvios):
    """Feixe de traços saindo do centro (usado no Claude)."""
    n = len(comprimentos)
    d = []
    for i, (r1, dv) in enumerate(zip(comprimentos, desvios)):
        ang = -90 + i * 360 / n + dv
        x0, y0 = ponto(cx, cy, r0, ang)
        x1, y1 = ponto(cx, cy, r1, ang)
        d.append(f"M{_n(x0)} {_n(y0)} L{_n(x1)} {_n(y1)}")
    return P(" ".join(d))


def engrenagem(cx, cy, r_ext, r_int, dentes, meio_int=11.5, meio_ext=7):
    passo = 360 / dentes
    d = []
    for k in range(dentes):
        t = -90 + k * passo
        a = ponto(cx, cy, r_int, t - meio_int)
        b = ponto(cx, cy, r_ext, t - meio_ext)
        c = ponto(cx, cy, r_ext, t + meio_ext)
        e = ponto(cx, cy, r_int, t + meio_int)
        f = ponto(cx, cy, r_int, t + passo - meio_int)
        if k == 0:
            d.append(f"M{_n(a[0])} {_n(a[1])}")
        d.append(f"L{_n(b[0])} {_n(b[1])}")
        d.append(f"A{_n(r_ext)} {_n(r_ext)} 0 0 1 {_n(c[0])} {_n(c[1])}")
        d.append(f"L{_n(e[0])} {_n(e[1])}")
        d.append(f"A{_n(r_int)} {_n(r_int)} 0 0 1 {_n(f[0])} {_n(f[1])}")
    d.append("Z")
    return P(" ".join(d))


# Formas reaproveitadas
BALAO = "M40 77 A30 30 0 1 1 48.8 86.6 L34 96 Z"               # balão de conversa
DOCUMENTO = "M40 30 H72 L90 48 V98 H40 Z M72 30 V48 H90"       # folha com dobra
PECA = ("M34 46 H50 A9 9 0 1 1 66 46 H82 V61 A9 9 0 1 1 82 77 "
        "V94 H34 Z")                                            # peça de quebra-cabeça
NUVEM = "M44 92 A12 12 0 1 1 45.1 68.1 A19 19 0 1 1 82.9 64.2 A14 14 0 1 1 85 92 Z"


# ── Glifos ────────────────────────────────────────────────────────────────
# chave -> (cor, svg)
GLIFOS = {
    # Dock
    "fedora": (BRANCO,
        P("M96 64 V90 Q96 96 90 96 H64 A32 32 0 1 1 96 64 Z")
        + P("M58 84 V60 A12 12 0 0 1 70 48 H74 M50 68 H72")),
    "arquivos": (AMBAR,
        P("M32 44 Q32 38 38 38 H54 L62 46 H90 Q96 46 96 52 V86 Q96 92 90 92 "
          "H38 Q32 92 32 86 Z M32 58 H96")),
    "brave": (CORAL,
        P("M42 34 L52 28 H76 L86 34 L94 38 L90 70 Q86 84 64 98 Q42 84 38 70 L34 38 Z")
        + P("M54 60 L64 68 L74 60 M57 80 L64 84 L71 80")),
    "spotify": (MENTA,
        C(64, 64, 33)
        + P("M45 53 Q64 46 84 55 M48 65 Q64 60 80 67 M51 77 Q64 72 76 79")),
    "deezer": (AMBAR,
        P("M36 94 V74 M50 94 V56 M64 94 V36 M78 94 V60 M92 94 V78")),
    "vscode": (BRANCO,
        P("M36 54 L88 98 V30 L36 74 Z")),
    "claude": (CORAL,
        raios(64, 64, 6,
              [34, 28, 33, 27, 34, 29, 33, 27, 32, 28],
              [0, 4, -3, 5, -2, 3, -4, 2, -3, 4])),
    "karere": (MENTA,
        P(BALAO) + P("M60 46 L54 50 C50 62 63 77 77 75 L81 69")),
    "discord": (BRANCO,
        P("M42 40 Q52 34 57 38 H71 Q76 34 86 40 Q97 58 95 80 Q87 88 78 88 L74 82 "
          "Q64 86 54 82 L50 88 Q41 88 33 80 Q31 58 42 40 Z")
        + D(53, 64, 5.5) + D(75, 64, 5.5)),
    "thunderbird": (AMBAR,
        R(32, 40, 64, 48, 8) + P("M36 46 L64 68 L92 46")),
    "terminal": (MENTA,
        P("M36 42 L58 62 L36 82 M66 84 H94")),
    "editor": (BRANCO,
        P("M32 46 H64 M32 62 H54 M32 78 H44")
        + P("M84 36 L94 46 L66 74 L54 78 L58 66 Z")),
    "writer": (BRANCO,
        P(DOCUMENTO) + P("M50 62 H80 M50 74 H80 M50 86 H70")),
    "calculadora": (AMBAR,
        P("M46 34 V58 M34 46 H58 M70 46 H94 "
          "M38 74 L54 90 M54 74 L38 90 M70 77 H94 M70 89 H94")),
    "calendario": (CORAL,
        R(32, 38, 64, 58, 10) + P("M32 54 H96 M48 30 V44 M80 30 V44")
        + D(48, 68, 4) + D(64, 68, 4) + D(80, 68, 4)
        + D(48, 82, 4) + D(64, 82, 4)),

    # Grade
    "configuracoes": (BRANCO,
        engrenagem(64, 64, 33, 25, 8) + C(64, 64, 10)),
    "programas": (AMBAR,
        P("M36 48 H92 L87 92 Q86 96 82 96 H46 Q42 96 41 92 Z")
        + P("M52 48 V42 A12 12 0 0 1 76 42 V48")),
    "ajustes": (MENTA,
        P("M32 44 H62 M82 44 H96 M32 64 H40 M60 64 H96 M32 84 H68 M88 84 H96")
        + C(72, 44, 8) + C(50, 64, 8) + C(78, 84, 8)),
    "extensoes": (MENTA, P(PECA)),
    "gerenciador-extensoes": (CORAL,
        P(PECA) + P("M58 60 V82 M50 74 L58 82 L66 74")),
    "firefox": (AMBAR,
        C(67, 62, 15)
        + P("M54 34 C32 45 30 82 52 92 C72 100 94 88 96 66 C96 54 92 46 85 39 "
            "L87 27 L76 34 Q71 33 65 33")),
    "vivaldi": (CORAL,
        C(64, 64, 33) + P("M48 50 L64 80 L80 50")),
    "btop": (MENTA,
        R(30, 38, 68, 52, 10) + P("M40 70 H50 L56 58 L64 80 L72 52 L78 68 H88")),
    "ytmdesktop": (CORAL,
        C(64, 64, 33) + P("M57 50 L80 64 L57 78 Z")),
    "audacious": (AMBAR,
        P("M50 84 V44 L88 36 V76") + D(43, 85, 8) + D(81, 77, 8)),
    "video": (BRANCO,
        R(30, 38, 68, 52, 12) + P("M57 52 L76 64 L57 76 Z")),
    "abdm": (MENTA,
        P("M64 32 V72 M48 56 L64 72 L80 56 M36 78 V92 H92 V78")),
    "localsend": (MENTA,
        P("M32 62 L96 34 L82 94 L62 74 Z M62 74 L96 34 M62 74 V90 L72 82")),
    "solanum": (CORAL,
        C(64, 70, 27) + P("M52 40 L64 46 L76 40 M64 46 V32")
        + P("M64 70 V56 M64 70 L74 76")),
    "spruce": (MENTA,
        P("M64 28 L44 56 H54 L38 80 H90 L74 56 H84 Z M64 80 V98")),
    "openlogi": (BRANCO,
        R(42, 30, 44, 68, 22) + P("M64 30 V56 M42 56 H86")),
    "dspy": (AMBAR,
        C(56, 56, 23) + P("M73 73 L94 94")
        + D(47, 56, 4) + D(56, 56, 4) + D(65, 56, 4)),
    "flameshot": (CORAL,
        P("M32 50 V32 H50 M78 32 H96 V50 M96 78 V96 H78 M50 96 H32 V78")
        + P("M64 46 C76 58 78 68 72 76 A12 12 0 0 1 56 76 C50 66 56 58 64 46 Z")),
    "whatsapp-web": (MENTA,
        P(BALAO) + P("M38 62 H94") + E(66, 62, 12, 30)),

    # Pasta Sistema
    "baobab": (AMBAR,
        C(64, 64, 32) + C(64, 64, 12)
        + P("M64 32 V52 M74.4 70 L91.7 80 M53.6 70 L36.3 80")),
    "discos": (BRANCO,
        R(30, 42, 68, 44, 12) + P("M42 64 H64") + D(84, 64, 5)),
    "logs": (CORAL,
        D(38, 44, 5) + D(38, 64, 5) + D(38, 84, 5)
        + P("M52 44 H94 M52 64 H86 M52 84 H90")),
    "controle-parental": (MENTA,
        P("M64 30 L92 40 V62 C92 80 80 92 64 98 C48 92 36 80 36 62 V40 Z")
        + C(64, 56, 8) + P("M50 82 A14 13 0 0 1 78 82")),
    "monitor-sistema": (BRANCO,
        P("M36.3 86 A32 32 0 1 1 91.7 86") + P("M64 70 L80 50") + D(64, 70, 6)),

    # Pasta Utilitários
    "decibels": (CORAL,
        P("M34 56 V72 M44 46 V82 M54 36 V92 M64 50 V78 M74 40 V88 "
          "M84 52 V76 M94 60 V68")),
    "conexoes": (MENTA,
        R(30, 34, 68, 46, 8) + P("M52 94 H76 M64 80 V94")
        + P("M46 50 H80 L74 44 M82 64 H48 L54 70")),
    "papers": (CORAL,
        P("M64 44 C54 36 40 36 32 40 V88 C40 84 54 84 64 92 "
          "C74 84 88 84 96 88 V40 C88 36 74 36 64 44 Z M64 44 V92")),
    "fontes": (BRANCO,
        P("M28 92 L48 36 L68 92 M36 74 H60") + C(84, 80, 10) + P("M94 66 V92")),
    "imagens": (AMBAR,
        R(30, 36, 68, 56, 10) + P("M30 84 L54 62 L70 78 L78 70 L98 88") + C(80, 54, 6)),
    "contatos": (AMBAR,
        C(64, 48, 13) + P("M38 94 C38 78 50 70 64 70 C78 70 90 78 90 94")),
    "relogios": (BRANCO,
        C(64, 64, 33) + P("M64 64 V44 M64 64 L78 72")),
    "clima": (BRANCO,
        '<defs><mask id="sem-nuvem" maskUnits="userSpaceOnUse" x="0" y="0" width="128" height="128">'
        '<rect width="128" height="128" fill="#fff" stroke="none"/>'
        f'<path d="{NUVEM}" fill="#000" stroke="#000" stroke-width="14"/></mask></defs>'
        '<g mask="url(#sem-nuvem)">' + C(80, 43, 13) + '</g>' + P(NUVEM)),
    "mapas": (MENTA,
        P("M32 40 L52 32 L76 40 L96 32 V88 L76 96 L52 88 L32 96 Z M52 32 V88 M76 40 V96")),
    "scanner": (BRANCO,
        R(30, 62, 68, 30, 10) + P("M36 50 L92 38") + P("M44 77 H70") + D(84, 77, 4)),
    "boxes": (AMBAR,
        P("M64 30 L92 46 V80 L64 96 L36 80 V46 Z M36 46 L64 62 L92 46 M64 62 V96")),
    "camera": (BRANCO,
        P("M38 44 H48 L54 36 H74 L80 44 H90 Q98 44 98 52 V84 Q98 92 90 92 H38 "
          "Q30 92 30 84 V52 Q30 44 38 44 Z") + C(64, 67, 13)),
    "caracteres": (CORAL,
        P("M38 92 H54 V84 A24 24 0 1 1 74 84 V92 H90")),
    "media-writer": (BRANCO,
        R(46, 52, 36, 46, 6) + P("M52 52 V32 H76 V52") + P("M64 62 V86 M56 78 L64 86 L72 78")),
    "tour": (MENTA,
        C(64, 64, 33) + P("M64 42 L72 64 L64 86 L56 64 Z")),
    "ajuda": (MENTA,
        C(64, 64, 33) + P("M54 54 A10 10 0 1 1 68 63 Q64 66 64 72") + D(64, 84, 4.5)),

    # Pasta Escritório
    "calc": (MENTA,
        P(DOCUMENTO) + P("M50 60 H80 V88 H50 Z M65 60 V88 M50 74 H80")),
    "impress": (CORAL,
        P(DOCUMENTO) + C(65, 74, 13) + P("M65 74 V61 M65 74 H78")),
    "libreoffice": (BRANCO, P(DOCUMENTO)),

    # Outros apps
    "vlc": (AMBAR,
        P("M56 32 H72 L88 86 H40 Z M47 62 H81") + P("M30 94 H98")),
}


# ── Pastas e lugares ──────────────────────────────────────────────────────
# Pasta grande; o símbolo vai no corpo, centrado em (64,74).
PASTA = ("M30 40 Q30 34 36 34 H54 L62 42 H92 Q98 42 98 48 V88 Q98 94 92 94 "
         "H36 Q30 94 30 88 Z M30 54 H98")


def pasta(simbolo="", cor=AMBAR):
    return (cor, P(PASTA) + simbolo)


LIXEIRA = "M38 44 L42 90 Q43 96 49 96 H79 Q85 96 86 90 L90 44"

GLIFOS.update({
    "pasta": pasta(),
    "pasta-documentos": pasta(P("M52 65 H76 M52 74 H76 M52 83 H68")),
    "pasta-downloads": pasta(P("M64 62 V84 M56 76 L64 84 L72 76")),
    "pasta-musica": pasta(P("M68 83 V63 H77") + D(62, 83, 6)),
    "pasta-imagens": pasta(P("M50 85 L60 72 L70 85") + D(75, 66, 4)),
    "pasta-videos": pasta(P("M58 64 L74 74 L58 84 Z")),
    "pasta-modelos": pasta(P("M56 63 H67 L73 69 V85 H56 Z")),
    "pasta-publica": pasta(C(64, 68, 5) + P("M54 86 A10 9 0 0 1 74 86")),
    "pasta-projetos": pasta(P("M56 65 L49 74 L56 83 M72 65 L79 74 L72 83")),
    "pasta-remota": pasta(P("M52 72 Q64 62 76 72 M57 79 Q64 73 71 79") + D(64, 85, 3.5)),
    "pasta-soltar": pasta(P("M64 64 V84 M54 74 H74")),
    "pasta-pessoal": pasta(P("M52 76 L64 64 L76 76 M56 72 V86 H72 V72")),
    "pasta-area-de-trabalho": pasta(R(51, 63, 26, 16, 3) + P("M64 79 V86 M58 86 H70")),
    "favoritos": (CORAL, P("M44 30 H84 V98 L64 82 L44 98 Z")),
    "servidor": (BRANCO,
        R(32, 34, 64, 26, 8) + R(32, 68, 64, 26, 8)
        + P("M44 47 H62 M44 81 H62") + D(82, 47, 4) + D(82, 81, 4)),
    "rede": (MENTA,
        C(64, 40, 9) + C(40, 86, 9) + C(88, 86, 9)
        + P("M59 48 L45 78 M69 48 L83 78 M49 86 H79")),
    "lixeira": (BRANCO,
        P("M30 44 H98 M52 44 V36 Q52 32 56 32 H72 Q76 32 76 36 V44")
        + P(LIXEIRA) + P("M56 56 V84 M72 56 V84")),
    "lixeira-cheia": (BRANCO,
        P("M32 40 L94 28 M54 36 L52 30 Q51 26 55 25 L70 22 Q74 21 75 25 L76 31")
        + P(LIXEIRA) + P("M50 62 L58 52 L68 58 L78 50 M50 76 H78")),

    # Dispositivos
    "fones": (MENTA,
        P("M36 78 V64 A28 28 0 0 1 92 64 V78") + R(32, 70, 14, 24, 6) + R(82, 70, 14, 24, 6)),
    "headset": (MENTA,
        P("M36 76 V62 A28 28 0 0 1 92 62 V76") + R(32, 66, 14, 22, 6) + R(82, 66, 14, 22, 6)
        + P("M89 88 Q88 96 76 96") + D(70, 96, 4)),
    "webcam": (BRANCO,
        C(64, 54, 24) + C(64, 54, 8) + P("M64 78 V92 M48 94 H80")),
    "computador": (BRANCO,
        P("M38 40 Q38 34 44 34 H84 Q90 34 90 40 V80 H38 Z M28 90 H100")),
    "disco": (BRANCO,
        R(30, 42, 68, 44, 12) + P("M42 64 H64") + D(84, 64, 5)),
    "multidisco": (BRANCO,
        R(30, 32, 68, 28, 8) + R(30, 68, 68, 28, 8) + D(84, 46, 4) + D(84, 82, 4)),
    "drive-optico": (BRANCO,
        R(30, 58, 68, 32, 8) + P("M42 74 H62 M36 46 H92") + D(84, 74, 4)),
    "pendrive": (BRANCO,
        R(46, 52, 36, 46, 6) + P("M52 52 V32 H76 V52") + D(58, 42, 3) + D(70, 42, 3)),
    "leitor-ebook": (BRANCO,
        R(38, 30, 52, 68, 8) + P("M48 46 H80 M48 58 H80 M48 70 H70") + D(64, 86, 3.5)),
    "controle": (CORAL,
        P("M44 46 H84 Q96 46 98 60 L100 80 Q101 92 90 90 L80 82 H48 L38 90 "
          "Q27 92 28 80 L30 60 Q32 46 44 46 Z")
        + P("M46 58 V70 M40 64 H52") + D(80, 60, 4) + D(86, 69, 4)),
    "teclado": (BRANCO,
        R(28, 40, 72, 48, 8)
        + "".join(D(x, y, 3) for y in (54, 66) for x in (40, 52, 64, 76, 88))
        + P("M48 77 H80")),
    "mouse": (MENTA, R(42, 30, 44, 68, 22) + P("M64 30 V56 M42 56 H86")),
    "mesa-digitalizadora": (BRANCO,
        R(30, 36, 68, 56, 8) + P("M44 76 Q54 54 64 68 T84 58")),
    "cartao-sd": (AMBAR,
        P("M44 30 H76 L88 42 V92 Q88 98 82 98 H46 Q40 98 40 92 V36 Q40 30 44 30 Z")
        + P("M54 40 V50 M64 40 V50 M74 44 V50")),
    "cd": (BRANCO, C(64, 64, 32) + C(64, 64, 9) + P("M64 43 A21 21 0 0 1 85 64")),
    "microfone": (CORAL,
        R(52, 30, 24, 42, 12) + P("M40 60 A24 24 0 0 0 88 60 M64 84 V96 M52 96 H76")),
    "celular": (BRANCO, R(44, 30, 40, 68, 10) + P("M58 88 H70")),
    "impressora": (BRANCO,
        P("M44 50 V32 H84 V50") + R(30, 50, 68, 32, 8) + P("M44 70 V96 H84 V70") + D(86, 62, 3.5)),
    "impressora-rede": (MENTA,
        P("M44 50 V32 H84 V50") + R(30, 50, 68, 32, 8) + P("M44 70 V96 H84 V70") + D(86, 62, 3.5)),
    "monitor": (BRANCO,
        R(30, 34, 68, 46, 8) + P("M52 94 H76 M64 80 V94")),
})


# ── Mapa de apps ──────────────────────────────────────────────────────────
# (rótulo, seções, glifo, ids .desktop, nomes extras de ícone)
# O nome do arquivo SVG vem do Icon= lido no .desktop instalado; "extras" são
# nomes reais vistos no sistema que o app também usa (ex.: ícone de janela).
# A origem especial "os-release:LOGO" lê o LOGO= de /etc/os-release.
APPS = [
    # Dock
    ("Fedora", ["Dock"], "fedora", ["os-release:LOGO"], []),
    ("Arquivos", ["Dock"], "arquivos", ["org.gnome.Nautilus.desktop"], []),
    ("Brave", ["Dock"], "brave", ["brave-origin.desktop"], []),
    ("Spotify", ["Dock"], "spotify", ["spotify.desktop"], []),
    ("Deezer", ["Dock"], "deezer", ["dev.aunetx.deezer.desktop", "deezer-desktop.desktop"], []),
    ("VS Code", ["Dock"], "vscode", ["com.microsoft.VSCode.desktop"], []),
    ("Claude", ["Dock"], "claude", ["claude-desktop-unofficial.desktop"], ["claude-desktop"]),
    ("Karere", ["Dock"], "karere", ["io.github.tobagin.karere.desktop"], []),
    ("Discord", ["Dock"], "discord", ["discord.desktop"], []),
    ("Thunderbird", ["Dock"], "thunderbird", ["net.thunderbird.Thunderbird.desktop"], []),
    ("Terminal", ["Dock"], "terminal", ["org.gnome.Ptyxis.desktop"], []),
    ("Editor de texto", ["Dock"], "editor", ["org.gnome.TextEditor.desktop"], []),
    ("LibreOffice Writer", ["Dock", "Escritório"], "writer", ["libreoffice-writer.desktop"], []),
    ("Calculadora", ["Dock"], "calculadora", ["org.gnome.Calculator.desktop"], []),
    ("Calendário", ["Dock"], "calendario", ["org.gnome.Calendar.desktop"], []),

    # Grade
    ("Configurações", ["Grade"], "configuracoes", ["org.gnome.Settings.desktop"], []),
    ("Programas", ["Grade"], "programas", ["org.gnome.Software.desktop"], []),
    ("Ajustes", ["Grade"], "ajustes", ["org.gnome.tweaks.desktop"], []),
    ("Gerenciador de extensões", ["Grade"], "gerenciador-extensoes",
     ["com.mattjakeman.ExtensionManager.desktop"], []),
    ("Extensões", ["Grade"], "extensoes",
     ["org.gnome.Extensions.desktop", "org.gnome.Shell.Extensions.desktop"], []),
    ("Firefox", ["Grade"], "firefox", ["org.mozilla.firefox.desktop"], []),
    ("Vivaldi", ["Grade"], "vivaldi", ["vivaldi-stable.desktop"], []),
    ("btop++", ["Grade"], "btop", ["btop.desktop"], []),
    ("YTMDesktop", ["Grade"], "ytmdesktop", ["app.ytmdesktop.ytmdesktop.desktop"], []),
    ("Audacious", ["Grade"], "audacious", ["audacious.desktop"], []),
    ("Reprodutor de vídeo", ["Grade", "Utilitários"], "video", ["org.gnome.Showtime.desktop"], []),
    ("AB Download Manager", ["Grade"], "abdm", ["com.abdownloadmanager.abdownloadmanager.desktop"], []),
    ("LocalSend", ["Grade"], "localsend", ["org.localsend.localsend_app.desktop"], []),
    ("Solanum", ["Grade"], "solanum", ["org.gnome.Solanum.desktop"], []),
    ("Spruce", ["Grade"], "spruce", ["io.github.shonubot.Spruce.desktop"], []),
    ("OpenLogi", ["Grade"], "openlogi", ["openlogi.desktop"], []),
    ("D-Spy", ["Grade"], "dspy", ["org.gnome.dspy.desktop"], []),
    ("Flameshot", ["Grade"], "flameshot", ["org.flameshot.Flameshot.desktop"], []),
    ("WhatsApp Web", ["Grade"], "whatsapp-web",
     ["brave-hnpfjngllnobngcgfapefoaidbinmjnm-Default.desktop"], []),

    # Pasta Sistema
    ("Analisador de disco", ["Sistema"], "baobab", ["org.gnome.baobab.desktop"], []),
    ("Discos", ["Sistema"], "discos", ["org.gnome.DiskUtility.desktop"], []),
    ("Logs", ["Sistema"], "logs", ["org.gnome.Logs.desktop"], []),
    ("Controle parental", ["Sistema"], "controle-parental",
     ["org.freedesktop.MalcontentControl.desktop"], []),
    ("Monitor do sistema", ["Sistema"], "monitor-sistema",
     ["org.gnome.SystemMonitor.desktop", "gnome-system-monitor-kde.desktop"], []),

    # Pasta Utilitários
    ("Reprodutor de áudio", ["Utilitários"], "decibels", ["org.gnome.Decibels.desktop"], []),
    ("Conexões", ["Utilitários"], "conexoes", ["org.gnome.Connections.desktop"], []),
    ("Visualizador de documentos", ["Utilitários"], "papers", ["org.gnome.Papers.desktop"], []),
    ("Fontes", ["Utilitários"], "fontes", ["org.gnome.font-viewer.desktop"], []),
    ("Visualizador de imagens", ["Utilitários"], "imagens", ["org.gnome.Loupe.desktop"], []),
    ("Contatos", ["Utilitários"], "contatos", ["org.gnome.Contacts.desktop"], []),
    ("Relógios", ["Utilitários"], "relogios", ["org.gnome.clocks.desktop"], []),
    ("Clima", ["Utilitários"], "clima", ["org.gnome.Weather.desktop"], []),
    ("Mapas", ["Utilitários"], "mapas", ["org.gnome.Maps.desktop"], []),
    ("Digitalizador", ["Utilitários"], "scanner", ["org.gnome.SimpleScan.desktop"], []),
    ("Boxes", ["Utilitários"], "boxes", ["org.gnome.Boxes.desktop"], []),
    ("Câmera", ["Utilitários"], "camera", ["org.gnome.Snapshot.desktop"], []),
    ("Caracteres", ["Utilitários"], "caracteres", ["org.gnome.Characters.desktop"], []),
    ("Fedora Media Writer", ["Utilitários"], "media-writer",
     ["org.fedoraproject.MediaWriter.desktop"], []),
    ("Tour", ["Utilitários"], "tour", ["org.gnome.Tour.desktop"], []),
    ("Ajuda", ["Utilitários"], "ajuda", ["org.gnome.Yelp.desktop"], []),

    # Pasta Escritório
    ("LibreOffice Calc", ["Escritório"], "calc", ["libreoffice-calc.desktop"], []),
    ("LibreOffice Impress", ["Escritório"], "impress", ["libreoffice-impress.desktop"], []),
    ("LibreOffice", ["Escritório"], "libreoffice", ["libreoffice-startcenter.desktop"], []),

    # Outros apps visíveis
    ("VLC", ["Outros apps"], "vlc", ["vlc.desktop"], []),
]


# ── Ícones fixos (não vêm de .desktop) ────────────────────────────────────
# (rótulo, seção, glifo, nomes de ícone, contexto/pasta em scalable/)
# Nomes iguais aos do Adwaita, para substituí-lo onde o GNOME os usa.
ICONES_FIXOS = [
    ("Pasta", "Lugares", "pasta", ["folder"], "places"),
    ("Documentos", "Lugares", "pasta-documentos", ["folder-documents"], "places"),
    ("Downloads", "Lugares", "pasta-downloads", ["folder-download"], "places"),
    ("Músicas", "Lugares", "pasta-musica", ["folder-music"], "places"),
    ("Imagens", "Lugares", "pasta-imagens", ["folder-pictures"], "places"),
    ("Vídeos", "Lugares", "pasta-videos", ["folder-videos"], "places"),
    ("Modelos", "Lugares", "pasta-modelos", ["folder-templates"], "places"),
    ("Público", "Lugares", "pasta-publica", ["folder-publicshare"], "places"),
    ("Projetos", "Lugares", "pasta-projetos", ["folder-projects"], "places"),
    ("Pasta remota", "Lugares", "pasta-remota", ["folder-remote"], "places"),
    ("Soltar na pasta", "Lugares", "pasta-soltar", ["folder-drag-accept"], "places"),
    ("Pasta pessoal", "Lugares", "pasta-pessoal", ["user-home"], "places"),
    ("Área de trabalho", "Lugares", "pasta-area-de-trabalho", ["user-desktop"], "places"),
    ("Favoritos", "Lugares", "favoritos", ["user-bookmarks"], "places"),
    ("Servidor", "Lugares", "servidor", ["network-server"], "places"),
    ("Rede", "Lugares", "rede", ["network-workgroup"], "places"),
    ("Lixeira", "Lugares", "lixeira", ["user-trash"], "places"),
    ("Lixeira cheia", "Lugares", "lixeira-cheia", ["user-trash-full"], "places"),

    ("Fones", "Dispositivos", "fones", ["audio-headphones"], "devices"),
    ("Headset", "Dispositivos", "headset", ["audio-headset"], "devices"),
    ("Webcam", "Dispositivos", "webcam", ["camera-web"], "devices"),
    ("Computador", "Dispositivos", "computador", ["computer"], "devices"),
    ("Disco rígido", "Dispositivos", "disco", ["drive-harddisk"], "devices"),
    ("Vários discos", "Dispositivos", "multidisco", ["drive-multidisk"], "devices"),
    ("Drive óptico", "Dispositivos", "drive-optico", ["drive-optical"], "devices"),
    ("Mídia removível", "Dispositivos", "pendrive", ["drive-removable-media", "media-removable"], "devices"),
    ("Leitor de e-book", "Dispositivos", "leitor-ebook", ["ebook-reader"], "devices"),
    ("Controle de jogo", "Dispositivos", "controle", ["input-gaming"], "devices"),
    ("Teclado", "Dispositivos", "teclado", ["input-keyboard"], "devices"),
    ("Mouse", "Dispositivos", "mouse", ["input-mouse"], "devices"),
    ("Mesa digitalizadora", "Dispositivos", "mesa-digitalizadora", ["input-tablet"], "devices"),
    ("Cartão de memória", "Dispositivos", "cartao-sd", ["media-flash"], "devices"),
    ("CD/DVD", "Dispositivos", "cd", ["media-optical"], "devices"),
    ("Microfone", "Dispositivos", "microfone", ["microphone"], "devices"),
    ("Celular", "Dispositivos", "celular", ["phone"], "devices"),
    ("Impressora", "Dispositivos", "impressora", ["printer"], "devices"),
    ("Impressora de rede", "Dispositivos", "impressora-rede", ["printer-network"], "devices"),
    ("Scanner", "Dispositivos", "scanner", ["scanner"], "devices"),
    ("Monitor", "Dispositivos", "monitor", ["video-display"], "devices"),
]
