"""Fontes dos ícones do Vitral-icons.

Cada app declara de onde vem o seu logo, nesta ordem de preferência:

  "original"            o ícone instalado do próprio app (SVG ou o maior PNG),
                        recortado ao conteúdo e centralizado no tile;
  "original-sem-fundo"  idem, mas removendo a placa de fundo do PNG;
  "simple:<slug>"       logo da biblioteca Simple Icons (fontes/simple-icons),
                        na cor oficial da marca;
  "desenho:<nome>"      desenho próprio (DESENHOS abaixo), para apps sem logo de
                        marca: GNOME, pastas, lixeira e dispositivos.

Os desenhos usam a paleta do template (tile.svg): coral, âmbar e menta como
cores de destaque, mais branco, prata e grafite, e "tinta" para glifos que
ficam direto sobre o tile (claro na variante escura, grafite na clara). Os
mesmos desenhos servem às duas variantes. Quadro 128x128, centrado em
(64,64), ocupando ~ x/y 28..100.
"""
from math import cos, radians, sin

# ── Simple Icons: cor oficial de cada marca (data/simple-icons.json) ──────
SIMPLE_ICONS = {
    "brave": ("#FB542B", "CC0-1.0"),
    "claude": ("#D97757", "CC0-1.0"),
    "deezer": ("#A238FF", "CC0-1.0"),
    "discord": ("#5865F2", "CC0-1.0"),
    "vivaldi": ("#EF3939", "CC-BY-4.0"),
    "whatsapp": ("#25D366", "CC0-1.0"),
}

# Versão colorida de alguns logos do Simple Icons, como o app mostra de fato:
# o logo vira um gradiente da marca e as partes vazadas do SVG (o leão do
# Brave) são preenchidas com outro gradiente, em vez de deixar ver o tile.
SIMPLE_ICONS_COLORIDOS = {
    "brave": {"gradiente": ("#FF6A1A", "#FF2A00"), "vazados": ("#FFFFFF", "#E2E2E6")},
}


# ── Primitivas ────────────────────────────────────────────────────────────
def _n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _pinta(cor):
    return cor if cor.startswith("#") else f"url(#{cor})"


def F(d, cor, extra=""):
    """Forma cheia."""
    return f'<path d="{d}" fill="{_pinta(cor)}"{extra}/>'


def FS(d, cor, w=4, extra=""):
    """Forma cheia com cantos arredondados (contorno da mesma cor)."""
    return (f'<path d="{d}" fill="{_pinta(cor)}" stroke="{_pinta(cor)}" '
            f'stroke-width="{_n(w)}"{extra}/>')


def S(d, cor, w, extra=""):
    return f'<path d="{d}" fill="none" stroke="{_pinta(cor)}" stroke-width="{_n(w)}"{extra}/>'


def FR(x, y, w, h, rx, cor, extra=""):
    return (f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" '
            f'rx="{_n(rx)}" fill="{_pinta(cor)}"{extra}/>')


def FC(cx, cy, r, cor, extra=""):
    return f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="{_pinta(cor)}"{extra}/>'


def SC(cx, cy, r, cor, w, extra=""):
    return (f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="none" '
            f'stroke="{_pinta(cor)}" stroke-width="{_n(w)}"{extra}/>')


def T(x, y, texto, tam, cor, familia="DejaVu Serif, serif", peso="700"):
    return (f'<text x="{_n(x)}" y="{_n(y)}" text-anchor="middle" font-family="{familia}" '
            f'font-size="{_n(tam)}" font-weight="{peso}" fill="{_pinta(cor)}">{texto}</text>')


def G(conteudo, transform):
    return f'<g transform="{transform}">{conteudo}</g>'


LUZ = ' fill-opacity="0.35"'          # realce branco translúcido
CINZA_LINHA = "#C4C4CA"
BUTT = ' stroke-linecap="butt"'


def ponto(cx, cy, r, ang):
    a = radians(ang)
    return cx + r * cos(a), cy + r * sin(a)


def raio(cx, cy, r0, r1, ang):
    x0, y0 = ponto(cx, cy, r0, ang)
    x1, y1 = ponto(cx, cy, r1, ang)
    return f"M{_n(x0)} {_n(y0)} L{_n(x1)} {_n(y1)}"


def arco(cx, cy, r, a0, a1):
    x0, y0 = ponto(cx, cy, r, a0)
    x1, y1 = ponto(cx, cy, r, a1)
    grande = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{_n(x0)} {_n(y0)} A{_n(r)} {_n(r)} 0 {grande} 1 {_n(x1)} {_n(y1)}"


def engrenagem(cx, cy, r_ext, r_int, dentes, meio_int, meio_ext):
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
    return " ".join(d) + " Z"


# ── Peças reaproveitadas ──────────────────────────────────────────────────
PASTA_FUNDO = "M29 40 Q29 32 37 32 H53 Q57 32 60 35 L64 39 H91 Q99 39 99 47 V58 H29 Z"
PASTA_FRENTE = "M29 54 Q29 47 36 47 H92 Q99 47 99 54 V89 Q99 97 91 97 H37 Q29 97 29 89 Z"
def pasta(emblema="", papel=False, cor="ambar"):
    s = F(PASTA_FUNDO, f"{cor}-escuro")
    if papel:
        s += FR(35, 40, 58, 22, 3, "branco")
    s += F(PASTA_FRENTE, cor)
    s += S("M35 51.5 H93", "#FFFFFF", 1.5, ' stroke-opacity="0.55"')
    return s + emblema


def drive(y, h, led="menta"):
    return (FR(29, y, 70, h, 10, "prata")
            + FR(31, y + 2, 66, h * 0.42, 8, "#FFFFFF", ' fill-opacity="0.25"')
            + FR(38, y + h / 2 - 3, 32, 6, 3, "grafite")
            + FC(87, y + h / 2, 4, led))


def tela(x, y, w, h):
    """Monitor com tela menta e pé prateado."""
    return (FR(x, y, w, h, 8, "prata")
            + FR(x + 5, y + 5, w - 10, h - 10, 4, "menta")
            + F(f"M{x + 5} {y + 5} H{x + w - 5} L{x + 5} {y + h - 22} Z", "#FFFFFF", ' fill-opacity="0.18"')
            + F(f"M56 {y + h} H72 L75 {y + h + 11} H53 Z", "prata")
            + FR(45, y + h + 11, 38, 5, 2.5, "prata"))


NUVEM = "M44 93 A12 12 0 1 1 45.1 69.1 A19 19 0 1 1 82.9 65.2 A14 14 0 1 1 85 93 Z"
PECA = "M34 46 H50 A9 9 0 1 1 66 46 H82 V61 A9 9 0 1 1 82 77 V94 H34 Z"
CONTROLE = ("M44 46 H84 Q96 46 99 60 L102 80 Q103 93 91 92 L80 82 H48 L37 92 "
            "Q25 93 26 80 L29 60 Q32 46 44 46 Z")


def impressora(led, extra=""):
    return (FR(41, 28, 46, 22, 3, "branco")
            + FR(27, 46, 74, 36, 10, "prata")
            + FR(29, 48, 70, 14, 8, "#FFFFFF", ' fill-opacity="0.25"')
            + FR(38, 68, 52, 4, 2, "grafite")
            + FR(41, 70, 46, 28, 3, "branco")
            + S("M48 80 H80 M48 88 H72", CINZA_LINHA, 3)
            + FC(90, 57, 3.5, led) + extra)


def fones(mic=False):
    s = (S("M34 76 V62 A30 30 0 0 1 94 62 V76", "prata", 6)
         + FR(27, 64, 19, 32, 8, "prata") + FR(82, 64, 19, 32, 8, "prata")
         + FR(41, 68, 6, 24, 3, "grafite") + FR(81, 68, 6, 24, 3, "grafite")
         + FR(29, 66, 6, 14, 3, "coral") + FR(93, 66, 6, 14, 3, "coral"))
    if mic:
        s += S("M37 94 Q38 100 52 100", "prata", 4) + FC(56, 100, 4.5, "coral")
    return s


FONTE_UI = "Adwaita Sans, Inter, Cantarell, sans-serif"


def calendario_hoje():
    """Calendário com a data de HOJE, no estilo do iOS escuro: dia da semana em
    coral em cima e o número do dia grande e fino. O tema é regerado todo dia
    à meia-noite (systemd/vitral-icons.timer) para a data acompanhar."""
    import datetime
    import locale
    try:
        locale.setlocale(locale.LC_TIME, "")
    except locale.Error:
        pass
    hoje = datetime.date.today()
    semana = hoje.strftime("%a").strip(".").capitalize()
    if (locale.getlocale(locale.LC_TIME)[0] or "").startswith("pt"):
        semana += "."          # "Seg.", "Ter.", ...
    return (T(64, 46, semana, 20, "#F0685A", FONTE_UI, "600")
            + T(64, 103, str(hoje.day), 62, "tinta", FONTE_UI, "300"))


# Lixeira no estilo do dock do Mac: cesto branco fosco e translúcido, visto um
# pouco de cima (boca oval com aro grosso), afunilando até a base arredondada.
# Cheia, mostra bolas de papel amassado (jornal e fotos) saindo pela boca e
# vistas, esmaecidas, através da parede fosca.
LX_BOCA = (64, 24, 39, 8.5)                     # cx, cy, rx, ry da boca
LX_CORPO = ("M25 24 A39 8.5 0 0 0 103 24 L97.2 108 Q96.6 116.5 88 117.8 "
            "Q64 121.5 40 117.8 Q31.4 116.5 30.8 108 Z")
LX_DEFS = (
    '<defs>'
    # parede: mais opaca nas laterais (mais material visto de lado), mais
    # translúcida no meio, com um realce vertical à esquerda
    '<linearGradient id="lx-parede" x1="25" y1="0" x2="103" y2="0" gradientUnits="userSpaceOnUse">'
    '<stop offset="0" stop-color="#E9EAEE" stop-opacity="0.98"/>'
    '<stop offset="0.08" stop-color="#FFFFFF" stop-opacity="0.97"/>'
    '<stop offset="0.2" stop-color="#FFFFFF" stop-opacity="0.82"/>'
    '<stop offset="0.5" stop-color="#F7F8FA" stop-opacity="0.66"/>'
    '<stop offset="0.82" stop-color="#F3F4F7" stop-opacity="0.74"/>'
    '<stop offset="0.94" stop-color="#FFFFFF" stop-opacity="0.96"/>'
    '<stop offset="1" stop-color="#E4E5EA" stop-opacity="0.98"/></linearGradient>'
    # leve sombreado de cima para baixo (mais claro embaixo, como na foto)
    '<linearGradient id="lx-luz" x1="0" y1="24" x2="0" y2="120" gradientUnits="userSpaceOnUse">'
    '<stop offset="0" stop-color="#9DA1AB" stop-opacity="0.16"/>'
    '<stop offset="0.35" stop-color="#FFFFFF" stop-opacity="0"/>'
    '<stop offset="1" stop-color="#FFFFFF" stop-opacity="0.35"/></linearGradient>'
    # interior visto pela boca
    '<linearGradient id="lx-dentro" x1="0" y1="15.5" x2="0" y2="32.5" gradientUnits="userSpaceOnUse">'
    '<stop offset="0" stop-color="#F2F3F6"/><stop offset="0.6" stop-color="#D5D8DE"/>'
    '<stop offset="1" stop-color="#C4C7CF"/></linearGradient>'
    f'<clipPath id="lx-corpo"><path d="{LX_CORPO}"/></clipPath>'
    '<clipPath id="lx-boca"><path d="M22 0 H106 V24 H22 Z"/>'
    '<ellipse cx="64" cy="24" rx="39" ry="8.5"/></clipPath>'
    '<filter id="lx-fosco" x="-10%" y="-10%" width="120%" height="120%">'
    '<feGaussianBlur stdDeviation="1.6"/></filter>'
    '</defs>')


def _amassado(cx, cy, raios, cores, centro=(0, 0), achatar=0.9, giro=0, linhas=False):
    """Bola de papel amassado: um leque de facetas triangulares de tons
    alternados a partir de um ponto interno, com contorno fino."""
    n = len(raios)
    vert = []
    for k, r in enumerate(raios):
        a = radians(giro + k * 360 / n)
        vert.append((cx + r * cos(a), cy + r * sin(a) * achatar))
    px, py = cx + centro[0], cy + centro[1]
    s = ""
    for k in range(n):
        (x0, y0), (x1, y1) = vert[k], vert[(k + 1) % n]
        d = f"M{_n(px)} {_n(py)} L{_n(x0)} {_n(y0)} L{_n(x1)} {_n(y1)} Z"
        cor = cores[k % len(cores)]
        s += (f'<path d="{d}" fill="{cor}" stroke="{cor}" stroke-width="0.6" '
              'stroke-linejoin="round"/>')
    contorno = "M" + " L".join(f"{_n(x)} {_n(y)}" for x, y in vert) + " Z"
    if linhas:                                   # texto do jornal
        r = min(raios) * 0.5
        for i, dy in enumerate((-0.45, -0.15, 0.15, 0.45)):
            y = cy + dy * r
            x0, x1 = cx - r + (i % 2) * 1.5, cx + r - (i % 3)
            s += S(f"M{_n(x0)} {_n(y + 0.8)} L{_n(x1)} {_n(y - 0.5)}",
                   "#8E9198", 0.7, ' stroke-opacity="0.4"')
    s += S(contorno, "#000000", 0.6, ' stroke-opacity="0.12" stroke-linejoin="round"')
    return s


JORNAL = ("#F7F7F9", "#E2E3E7", "#FFFFFF", "#D3D5DA", "#EEEFF2", "#DADCE0")
# Fotos amassadas: facetas coloridas da imagem intercaladas com o verso e a
# borda brancos do papel fotográfico.
FOTO_CORES = ("#F4F5F7", "#4A8FE0", "#3C7ACB", "#DFE1E5", "#5DB860", "#E8645A", "#FFFFFF", "#4CA352")
FOTO_POR_DO_SOL = ("#6AA6EA", "#F3F4F6", "#EE9A4C", "#4F86D2", "#DDDEE2", "#F0B35E")


def _papeis(dentro=False):
    """Bolas de papel: as de dentro (dentro=True) só aparecem borradas,
    através da parede fosca; as de cima enchem a boca e passam do aro."""
    if dentro:
        return (_amassado(46, 52, (15, 13, 16, 14, 15, 13, 14), JORNAL, (1, 1), giro=10)
                + _amassado(76, 48, (14, 12, 15, 13, 14, 12), FOTO_POR_DO_SOL, (-1, 0), giro=-20)
                + _amassado(60, 72, (16, 14, 15, 13, 16, 14, 15), JORNAL[3:] + JORNAL[:3], giro=5)
                + _amassado(85, 76, (12, 10, 13, 11, 12), FOTO_CORES, giro=40)
                + _amassado(40, 84, (12, 11, 13, 10, 12), JORNAL, giro=-30))
    s = ""
    s += _amassado(47, 22, (14, 12.5, 15, 13, 14.5, 12, 14, 13), JORNAL, (1.5, -1), giro=8, linhas=True)
    s += _amassado(84, 21, (14, 12, 14.5, 13, 13.5, 12.5, 14), JORNAL[2:] + JORNAL[:2], (-1, -1), giro=-15,
                   linhas=True)
    s += _amassado(65, 16, (13, 11.5, 14, 12, 13, 11, 12.5, 12), FOTO_CORES, (-1, 1), giro=-12)
    s += _amassado(37, 28, (11, 10, 11.5, 9.5, 10.5, 10), JORNAL, (1, -0.5), giro=-5)
    s += _amassado(75, 27, (10.5, 9, 11, 9.5, 10, 9), FOTO_POR_DO_SOL, (0.5, 0.5), giro=20)
    s += _amassado(56, 30, (10, 9, 10.5, 9.5, 10), JORNAL[1:] + JORNAL[:1], (0, 0.5), giro=30, linhas=True)
    s += _amassado(92, 29, (8.5, 7.5, 9, 8), JORNAL, giro=15)
    return s


def lixeira(cheia=False):
    cx, cy, rx, ry = LX_BOCA
    boca = f'cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"'
    s = LX_DEFS
    s += '<ellipse cx="64" cy="119.5" rx="31" ry="3.2" fill="#000000" fill-opacity="0.18"/>'  # contato
    s += f'<ellipse {boca} fill="url(#lx-dentro)"/>'                  # interior pela boca
    s += f'<path d="{LX_CORPO}" fill="#FFFFFF" fill-opacity="0.35"/>'  # parede de trás
    if cheia:                                     # conteúdo visto (borrado) pela parede
        s += (f'<g clip-path="url(#lx-corpo)"><g filter="url(#lx-fosco)" opacity="0.8">'
              f'{_papeis(dentro=True)}{_papeis()}</g></g>')
    # parede da frente, fosca e translúcida
    s += f'<path d="{LX_CORPO}" fill="url(#lx-parede)"/>'
    s += f'<path d="{LX_CORPO}" fill="url(#lx-luz)"/>'
    s += S("M33.5 36 L37 110", "#FFFFFF", 3, ' stroke-opacity="0.75"')  # realce à esquerda
    s += S("M96.5 34 L92.6 110", "#FFFFFF", 1.6, ' stroke-opacity="0.6"')
    # contorno discreto para o cesto não sumir sobre fundo claro
    s += f'<path d="{LX_CORPO}" fill="none" stroke="#7C808A" stroke-opacity="0.35" stroke-width="0.8"/>'
    if cheia:                                     # papéis na boca e acima do aro
        s += f'<g clip-path="url(#lx-boca)">{_papeis()}</g>'
    # aro grosso da boca
    s += (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx - 1.6}" ry="{ry - 1.3}" fill="none" '
          'stroke="#9A9EA8" stroke-opacity="0.4" stroke-width="1"/>')
    s += f'<ellipse {boca} fill="none" stroke="#FFFFFF" stroke-width="3"/>'
    s += (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx + 1.5}" ry="{ry + 1.5}" fill="none" '
          'stroke="#7C808A" stroke-opacity="0.35" stroke-width="0.7"/>')
    # o conjunto (com os papéis acima do aro) cabe no quadro
    return G(s, "translate(64 64) scale(0.92) translate(-64 -62)")


# ── Desenhos próprios ─────────────────────────────────────────────────────
DESENHOS = {
    # Apps sem logo de marca
    "arquivos": pasta(papel=True, cor="azul"),  # azul da pasta do app Arquivos do iOS

    "terminal": (FR(29, 32, 70, 64, 12, "grafite")
                 + FR(33, 43, 62, 49, 7, "grafite-escuro")
                 + FC(38, 37.5, 2.3, "coral") + FC(45, 37.5, 2.3, "ambar") + FC(52, 37.5, 2.3, "menta")
                 + S("M42 56 L52 64.5 L42 73", "menta", 5)
                 + S("M57 76 H74", "branco", 5)),

    "editor": (FR(31, 29, 52, 70, 8, "branco")
               + S("M40 44 H74 M40 54 H74 M40 64 H66 M40 74 H58 M40 84 H62", CINZA_LINHA, 3.5)
               + G(FR(74, 40, 12, 40, 1.5, "ambar")
                   + FR(74, 32, 12, 9, 3, "coral")
                   + FR(74, 39, 12, 4, 0, "prata")
                   + F("M74 80 H86 L80 92 Z", "#F1D3A6")
                   + F("M78.2 88.5 H81.8 L80 92 Z", "grafite"),
                   "rotate(35 80 62) translate(2 2)")),

    "calculadora": (FR(36, 28, 56, 72, 13, "prata")
                    + FR(38, 30, 52, 26, 11, "#FFFFFF", ' fill-opacity="0.3"')
                    + FR(42, 34, 44, 16, 4, "grafite-escuro")
                    + S("M74 42 H80", "menta", 3)
                    + "".join(FC(x, y, 5.3, "ambar" if x == 78 else "grafite")
                              for y in (61, 74, 87) for x in (50, 64, 78))),

    "calendario": calendario_hoje(),

    "configuracoes": (F(engrenagem(64, 64, 36, 30, 12, 8.5, 5.5), "prata")
                      + FC(64, 64, 23, "grafite-escuro")
                      + FC(64, 64, 18, "prata")
                      + "".join(S(raio(64, 64, 8, 17, a), "grafite-escuro", 4) for a in (-90, 30, 150))
                      + FC(64, 64, 6, "grafite-escuro") + FC(64, 64, 3, "prata")),

    "programas": (S("M50 54 V45 A14 14 0 0 1 78 45 V54", "prata", 5)
                  + FS("M33 51 H95 L91 93 Q90 99 84 99 H44 Q38 99 37 93 Z", "ambar", 3)
                  + F("M35 53 H93 L92 62 H36 Z", "#FFFFFF", LUZ)
                  + FR(52, 64, 11, 11, 3, "coral") + FR(66, 64, 11, 11, 3, "menta")
                  + FR(52, 78, 11, 11, 3, "branco") + FR(66, 78, 11, 11, 3, "grafite")),

    "ajustes": (FR(31, 38, 66, 22, 11, "menta") + FC(86, 49, 8.5, "branco")
                + FR(31, 68, 66, 22, 11, "grafite") + FC(42, 79, 8.5, "prata")),

    "extensoes": G(FS(PECA, "menta", 4), "translate(64 64) scale(1.15) translate(-64.5 -63.5)"),

    "video": (FR(29, 36, 70, 56, 14, "coral")
              + FR(31, 38, 66, 22, 12, "#FFFFFF", ' fill-opacity="0.2"')
              + FS("M57 51 L78 64 L57 77 Z", "branco", 4)),

    # Pasta Sistema
    "baobab": (S(arco(64, 64, 27, -90, 60), "menta", 16, BUTT)
               + S(arco(64, 64, 27, 64, 190), "ambar", 16, BUTT)
               + S(arco(64, 64, 27, 194, 266), "coral", 16, BUTT)),

    "discos": drive(42, 44),

    "logs": (FR(31, 29, 66, 70, 12, "branco")
             + "".join(FC(44, y, 4.5, c) + S(f"M54 {y} H86", CINZA_LINHA, 4)
                       for y, c in ((46, "coral"), (60, "ambar"), (74, "menta"), (88, "grafite")))),

    "controle-parental": (F("M64 28 L94 39 V62 C94 82 81 94 64 100 C47 94 34 82 34 62 V39 Z", "menta")
                          + F("M64 28 L94 39 V48 L64 38 L34 48 V39 Z", "#FFFFFF", LUZ)
                          + FC(64, 57, 9, "branco")
                          + F("M47 85 C47 73 55 69 64 69 C73 69 81 73 81 85 Z", "branco")),

    "monitor-sistema": (S(arco(64, 72, 30, 150, 30), "grafite", 10, BUTT)
                        + S(arco(64, 72, 30, 150, 215), "menta", 10, BUTT)
                        + S(arco(64, 72, 30, 218, 278), "ambar", 10, BUTT)
                        + S(arco(64, 72, 30, 281, 330), "coral", 10, BUTT)
                        + S("M64 72 L82 52", "tinta", 5) + FC(64, 72, 7, "prata")),

    # Pasta Utilitários
    "decibels": "".join(S(f"M{x} {64 - h} V{64 + h}", c, 7)
                        for x, h, c in ((31, 7, "menta"), (42, 16, "menta"), (53, 26, "ambar"),
                                        (64, 33, "ambar"), (75, 22, "coral"), (86, 14, "coral"),
                                        (97, 6, "coral"))),

    "conexoes": (tela(29, 30, 70, 50)
                 + S("M46 47 H80 L74 41 M82 61 H48 L54 67", "branco", 4.5)),

    "papers": (F("M64 45 C54 38 37 38 27 42 V94 C37 90 54 90 64 97 C74 90 91 90 101 94 V42 "
                 "C91 38 74 38 64 45 Z", "coral")
               + F("M64 41 C55 34 40 34 31 37 V88 C40 85 55 85 64 91 Z", "branco")
               + F("M64 41 C73 34 88 34 97 37 V88 C88 85 73 85 64 91 Z", "branco")
               + F("M64 41 C73 34 88 34 97 37 V88 C88 85 73 85 64 91 Z", "#000000", ' fill-opacity="0.06"')
               + S("M38 50 Q46 47 56 50 M38 60 Q46 57 56 60 M38 70 Q46 67 56 70 "
                   "M72 50 Q82 47 90 50 M72 60 Q82 57 90 60 M72 70 Q82 67 90 70", CINZA_LINHA, 2.5)
               + S("M64 41 V91", CINZA_LINHA, 1.5)),

    "fontes": (FR(31, 31, 66, 66, 14, "branco")
               + T(53, 82, "A", 48, "grafite") + T(81, 82, "a", 36, "coral")),

    "imagens": (FR(29, 31, 70, 66, 10, "branco")
                + FR(35, 37, 58, 44, 5, "menta")
                + FC(80, 49, 6, "ambar")
                + F("M35 81 L55 56 L73 81 Z", "menta-escuro")
                + F("M54 81 L72 63 L93 81 Z", "coral")),

    "contatos": ('<defs><clipPath id="disco-contato"><circle cx="64" cy="64" r="35"/></clipPath></defs>'
                 + FC(64, 64, 35, "prata")
                 + f'<g clip-path="url(#disco-contato)">{FC(64, 54, 13, "branco")}{FC(64, 98, 26, "branco")}</g>'),

    "relogios": (FC(64, 64, 35, "branco")
                 + "".join(S(raio(64, 64, 28, 31, a), "grafite", 2.5) for a in range(0, 360, 30))
                 + S("M64 64 L64 45", "grafite", 5) + S("M64 64 L80 72", "grafite", 4)
                 + S("M64 72 L64 37", "coral", 2) + FC(64, 64, 3.5, "coral")),

    "clima": (FC(80, 48, 16, "ambar") + F(NUVEM, "branco")),

    "mapas": (F("M29 38 L52 30 V90 L29 98 Z", "menta")
              + F("M52 30 L76 38 V98 L52 90 Z", "menta-escuro")
              + F("M76 38 L99 30 V90 L76 98 Z", "menta")
              + S("M29 76 Q46 66 60 74 T99 66", "branco", 4)
              + F("M70 68 C61 56 58 51 58 47 A12 12 0 0 1 82 47 C82 51 79 56 70 68 Z", "coral")
              + FC(70, 47, 4.5, "branco")),

    "scanner": (F("M29 52 L95 38 Q99 37 99 41 V44 L31 60 Q29 60 29 58 Z", "grafite")
                + FR(29, 58, 70, 36, 10, "prata")
                + FR(31, 60, 66, 14, 8, "#FFFFFF", ' fill-opacity="0.25"')
                + S("M38 78 H72", "menta", 5) + FC(88, 78, 4, "menta")),

    "boxes": (FS("M64 28 L97 46 L64 64 L31 46 Z", "ambar", 3)
              + FS("M31 46 L64 64 V100 L31 82 Z", "ambar", 3)
              + FS("M97 46 V82 L64 100 V64 Z", "ambar-escuro", 3)
              + F("M64 28 L97 46 L64 64 L31 46 Z", "#FFFFFF", LUZ)),

    "camera": (FS("M38 44 H48 L53 37 H75 L80 44 H90 Q99 44 99 53 V86 Q99 95 90 95 H38 "
                  "Q29 95 29 86 V53 Q29 44 38 44 Z", "prata", 2)
               + FC(64, 69, 19, "grafite") + FC(64, 69, 14, "grafite-escuro")
               + FC(64, 69, 9, "menta-escuro") + FC(60, 65, 3, "#FFFFFF", ' fill-opacity="0.75"')
               + FC(89, 53, 3.5, "ambar")),

    "caracteres": "".join(FR(x, y, 31, 31, 8, "branco")
                          + T(x + 15.5, y + 23, ch, 21, cor, "DejaVu Sans, sans-serif")
                          for (x, y), ch, cor in (((31, 31), "Ω", "grafite"), ((66, 31), "A", "coral"),
                                                  ((31, 66), "&amp;", "menta"), ((66, 66), "π", "ambar"))),

    "tour": (S("M56 85 L59 94 M72 85 L69 94", "prata", 2)
             + FR(57, 93, 14, 9, 2.5, "ambar-escuro")
             + F("M64 27 C83 27 96 41 96 57 C96 70 84 80 73 87 H55 C44 80 32 70 32 57 "
                 "C32 41 45 27 64 27 Z", "coral")
             + F("M64 27 C73 27 78 42 78 57 C78 70 72 80 69 87 H59 C56 80 50 70 50 57 "
                 "C50 42 55 27 64 27 Z", "ambar")
             + F("M64 27 C67 27 69 42 69 57 C69 70 66 80 65 87 H63 C62 80 59 70 59 57 "
                 "C59 42 61 27 64 27 Z", "branco")
             + S("M44 38 C39 44 37 51 38 58", "#FFFFFF", 3, ' stroke-opacity="0.45"')),

    "ajuda": (SC(64, 64, 26, "branco", 17)
              + "".join(S(arco(64, 64, 26, a - 16, a + 16), "coral", 17, BUTT) for a in (45, 135, 225, 315))),

    # Lugares
    "favoritos": (FS("M43 28 H85 Q89 28 89 32 V99 L64 82 L39 99 V32 Q39 28 43 28 Z", "coral", 3)
                  + F("M43 28 H85 Q89 28 89 32 V40 H39 V32 Q39 28 43 28 Z", "#FFFFFF", LUZ)),
    "servidor": drive(30, 30) + drive(68, 30, "ambar"),
    "rede": (S("M64 40 L40 86 M64 40 L88 86 M40 86 H88", "prata", 5)
             + FC(64, 40, 11, "menta") + FC(40, 86, 11, "ambar") + FC(88, 86, 11, "coral")
             + FC(64, 40, 4, "branco") + FC(40, 86, 4, "branco") + FC(88, 86, 4, "branco")),
    "lixeira": lixeira(),
    "lixeira-cheia": lixeira(cheia=True),

    # Dispositivos
    "fones": fones(),
    "headset": fones(mic=True),
    "webcam": (FC(64, 54, 26, "prata") + FC(64, 54, 17, "grafite-escuro")
               + FC(64, 54, 10, "menta-escuro") + FC(60, 50, 3, "#FFFFFF", ' fill-opacity="0.75"')
               + FC(83, 40, 2.5, "coral")
               + FR(60, 78, 8, 10, 2, "prata") + F("M64 84 L76 94 H52 Z", "prata")
               + FR(44, 93, 40, 6, 3, "prata")),
    "computador": (FR(35, 31, 58, 44, 6, "prata") + FR(39, 35, 50, 36, 3, "menta")
                   + F("M39 35 H89 L39 60 Z", "#FFFFFF", ' fill-opacity="0.18"')
                   + F("M27 79 H101 L97 91 Q96 95 91 95 H37 Q32 95 31 91 Z", "prata")
                   + FR(56, 79, 16, 3, 1.5, "grafite")),
    "disco": drive(42, 44),
    "multidisco": drive(30, 30) + drive(68, 30),
    "drive-optico": (F("M38 57 A26 26 0 0 1 90 57 Z", "branco")
                     + S(arco(64, 57, 18, 180, 360), "menta", 3)
                     + F("M58 57 A6 6 0 0 1 70 57 Z", "fundo")
                     + drive(56, 36)),
    "pendrive": (FR(52, 26, 24, 24, 3, "prata")
                 + FR(57, 32, 5, 5, 1, "grafite") + FR(66, 32, 5, 5, 1, "grafite")
                 + FR(45, 46, 38, 54, 10, "coral")
                 + FR(47, 48, 34, 20, 8, "#FFFFFF", ' fill-opacity="0.22"')
                 + FC(64, 88, 4, "fundo")),
    "leitor-ebook": (FR(36, 26, 56, 76, 10, "grafite") + FR(41, 31, 46, 60, 4, "branco")
                     + S("M48 42 H80 M48 50 H80 M48 58 H80 M48 66 H74 M48 74 H80 M48 82 H68", CINZA_LINHA, 2.5)
                     + FR(58, 94, 12, 3, 1.5, "prata")),
    "controle": (FS(CONTROLE, "branco", 2)
                 + FR(39, 57, 6, 18, 2, "grafite") + FR(33, 63, 18, 6, 2, "grafite")
                 + FC(82, 58, 4.5, "coral") + FC(91, 66, 4.5, "menta")
                 + FC(73, 66, 4.5, "ambar") + FC(82, 74, 4.5, "grafite")),
    "teclado": (FR(24, 42, 80, 46, 10, "prata")
                + "".join(FR(x, y, 9, 8, 2, "branco") for y in (49, 61) for x in range(31, 92, 12))
                + FR(31, 73, 9, 8, 2, "branco") + FR(43, 73, 42, 8, 2, "branco")
                + FR(88, 73, 9, 8, 2, "ambar")),
    "mouse": (FR(42, 27, 44, 74, 22, "branco")
              + S("M64 27 V55 M43 55 H85", CINZA_LINHA, 2)
              + FR(61, 35, 6, 13, 3, "coral")),
    "mesa-digitalizadora": (FR(26, 34, 76, 60, 10, "grafite") + FR(32, 40, 64, 48, 4, "branco")
                            + S("M42 76 Q52 54 62 68 T84 56", "coral", 3.5)
                            + G(FR(86, 28, 6, 40, 3, "ambar") + F("M86 67 H92 L89 74 Z", "grafite"),
                                "rotate(28 89 50)")),
    "cartao-sd": (FS("M44 28 H78 L92 42 V92 Q92 99 85 99 H44 Q36 99 36 92 V35 Q36 28 44 28 Z", "grafite", 2)
                  + "".join(FR(x, 34, 5, 12, 1.5, "ambar") for x in (46, 55, 64, 73))
                  + FR(44, 58, 40, 32, 4, "ambar")
                  + T(64, 80, "SD", 16, "grafite-escuro", "DejaVu Sans, sans-serif")),
    "cd": (FC(64, 64, 35, "prata")
           + S(arco(64, 64, 25, 200, 250), "menta", 7, ' stroke-opacity="0.85"')
           + S(arco(64, 64, 25, 20, 70), "ambar", 7, ' stroke-opacity="0.85"')
           + S(arco(64, 64, 25, 290, 330), "coral", 7, ' stroke-opacity="0.85"')
           + FC(64, 64, 11, "branco") + FC(64, 64, 5, "fundo")),
    "microfone": (FR(51, 26, 26, 46, 13, "prata")
                  + S("M56 40 H72 M56 47 H72 M56 54 H72", "grafite", 2)
                  + FR(51, 61, 26, 4, 0, "coral")
                  + S("M40 58 A24 24 0 0 0 88 58 M64 82 V94", "prata", 5)
                  + FR(48, 93, 32, 6, 3, "prata")),
    "celular": (FR(42, 25, 44, 78, 12, "grafite") + FR(46, 29, 36, 70, 9, "menta")
                + FC(64, 66, 11, "ambar", ' fill-opacity="0.9"') + FC(72, 76, 8, "coral", ' fill-opacity="0.85"')
                + FR(57, 33, 14, 4.5, 2.25, "grafite-escuro")),
    "impressora": impressora("menta"),
    "impressora-rede": impressora("ambar", S("M27 36 Q34 29 41 36 M30.5 40 Q34 36.5 37.5 40", "menta", 3)),
    "monitor": tela(27, 30, 74, 52),
}



# ── Pastas (estilo macOS, avulsas, no azul do app Arquivos) ───────────────
PASTA_TRAS = "M10 31 Q10 22 19 22 H45 Q50 22 53 26 L57 31 H109 Q118 31 118 40 V99 Q118 108 109 108 H19 Q10 108 10 99 Z"
PASTA_FRENTE_MAC = "M10 47 Q10 39 18 39 H110 Q118 39 118 47 V99 Q118 108 109 108 H19 Q10 108 10 99 Z"
PASTA_FRENTE_ABERTA = "M18 54 H115 Q123 54 121.5 62 L113.5 101 Q112 108 104 108 H19 Q10 108 10 99 V62 Q10 54 18 54 Z"

# Emblemas das pastas especiais: função da cor, centrados em (64, 74).
EMBLEMAS = {
    "documentos": lambda c: S("M49 63 H79 M49 73 H79 M49 83 H70", c, 6),
    "downloads": lambda c: S("M64 57 V87 M52 76 L64 88 L76 76", c, 6),
    "imagens": lambda c: FS("M45 88 L57 69 L69 88 Z", c, 3) + FS("M62 88 L72 76 L83 88 Z", c, 3) + FC(77, 63, 5, c),
    "musica": lambda c: S("M71 84 V60 H82", c, 6) + FC(64, 84, 7.5, c),
    "videos": lambda c: FS("M56 60 L77 74 L56 88 Z", c, 4),
    "modelos": lambda c: S("M54 58 H69 L76 65 V90 H54 Z M69 58 V65 H76", c, 5),
    "publica": lambda c: FC(64, 64, 7, c) + S("M50 90 A14 13 0 0 1 78 90", c, 6),
    "remota": lambda c: S("M47 73 Q64 58 81 73 M55 81 Q64 73 73 81", c, 5.5) + FC(64, 89, 4, c),
    "projetos": lambda c: S("M56 63 L47 74 L56 85 M72 63 L81 74 L72 85", c, 6),
    "pessoal": lambda c: S("M48 76 L64 61 L80 76 M53 71 V89 H75 V71", c, 5.5),
    "area-de-trabalho": lambda c: S("M47 62 H81 V82 H47 Z M64 82 V89 M55 89 H73", c, 5),
}


PASTA_GRAVACAO = "#0459C4"   # sombra azul-escura dos emblemas "gravados"


def pasta_mac(emblema=None, aberta=False):
    s = F(PASTA_TRAS, "azul-escuro")
    if aberta:
        s += FR(22, 30, 84, 44, 3, "#F2F2F5") + FR(28, 25, 72, 44, 3, "branco")
    s += F(PASTA_FRENTE_ABERTA if aberta else PASTA_FRENTE_MAC, "azul")
    s += S("M16 57.5 H116" if aberta else "M15 42.5 H113", "#FFFFFF", 1.5, ' stroke-opacity="0.55"')
    if emblema:
        desenho = EMBLEMAS[emblema]
        # Leve gravação: o emblema escuro 1.5px abaixo e o branco por cima.
        s += G(desenho(PASTA_GRAVACAO), "translate(0 1.5)") + desenho("#FFFFFF")
    return s


DESENHOS.update({
    "pasta": pasta_mac(),
    "pasta-aberta": pasta_mac(aberta=True),
    **{f"pasta-{nome}": pasta_mac(nome) for nome in EMBLEMAS},
})


# ── Tipos de arquivo: folha dobrada com etiqueta colorida ─────────────────
FOLHA = "M32 10 H80 L102 32 V112 Q102 118 96 118 H32 Q26 118 26 112 V16 Q26 10 32 10 Z"
DOBRA = "M80 10 V26 Q80 32 86 32 H102 Z"

# categoria: (símbolo em função da cor, texto da etiqueta)
CATEGORIAS = {
    "documento": (lambda c: S("M40 44 H74 M40 54 H88 M40 64 H88 M40 74 H80", c, 4), "DOC"),
    "planilha": (lambda c: S("M40 42 H88 V80 H40 Z M56 42 V80 M72 42 V80 M40 55 H88 M40 67 H88", c, 3), "XLS"),
    "apresentacao": (lambda c: S("M40 79 H88", c, 3) + FR(45, 61, 9, 15, 2, c) + FR(59.5, 52, 9, 24, 2, c)
                     + FR(74, 43, 9, 33, 2, c), "PPT"),
    "pdf": (lambda c: S("M40 44 H70 M40 54 H88 M40 64 H88", c, 4) + S("M40 76 Q50 68 58 76 T76 74", c, 3.5), "PDF"),
    "imagem": (lambda c: FS("M40 79 L56 55 L70 79 Z", c, 3) + FS("M60 79 L73 63 L88 79 Z", c, 3)
               + FC(78, 48, 6, c), "IMG"),
    "audio": (lambda c: S("M70 75 V46 L85 50", c, 5) + FC(62, 75, 8, c), "MP3"),
    "video": (lambda c: FS("M54 45 L81 61 L54 77 Z", c, 4), "MP4"),
    "texto": (lambda c: S("M40 44 H80 M40 54 H88 M40 64 H88 M40 74 H70", c, 4), "TXT"),
    "codigo": (lambda c: S("M53 47 L41 61 L53 75 M75 47 L87 61 L75 75 M68 43 L60 79", c, 4.5), "&lt;/&gt;"),
    "compactado": (lambda c: "".join(FR(58 if i % 2 == 0 else 64, 12 + i * 6, 6, 4, 1, c) for i in range(10))
                   + FR(56, 72, 16, 12, 3, c) + FR(61, 75, 6, 6, 1.5, "branco"), "ZIP"),
    "executavel": (lambda c: F(engrenagem(64, 60, 17, 13, 8, 10, 7), c) + FC(64, 60, 5.5, "branco"), "EXE"),
}


def documento(categoria, cor):
    simbolo, rotulo = CATEGORIAS[categoria]
    return (F(FOLHA, "branco") + S(FOLHA, "#000000", 2, ' stroke-opacity="0.24"')
            + F(DOBRA, "#D3D3D9") + simbolo(cor)
            + FR(34, 88, 60, 20, 6, cor)
            + T(64, 102.5, rotulo, 12.5, "#FFFFFF", FONTE_UI, "700"))


# Nomes de ícone de cada categoria: todos os genéricos do Adwaita e os
# específicos mais comuns (o GNOME procura o específico antes do genérico).
MIMETIPOS = {
    "documento": ["x-office-document", "x-office-document-template", "application-vnd.oasis.opendocument.text",
                  "application-msword", "application-vnd.openxmlformats-officedocument.wordprocessingml.document",
                  "application-rtf", "x-office-addressbook", "font-x-generic", "application-certificate"],
    "planilha": ["x-office-spreadsheet", "x-office-spreadsheet-template", "application-vnd.oasis.opendocument.spreadsheet",
                 "application-vnd.ms-excel", "application-vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                 "text-csv"],
    "apresentacao": ["x-office-presentation", "x-office-presentation-template",
                     "application-vnd.oasis.opendocument.presentation", "application-vnd.ms-powerpoint",
                     "application-vnd.openxmlformats-officedocument.presentationml.presentation"],
    "pdf": ["application-pdf", "application-epub+zip"],
    "imagem": ["image-x-generic", "x-office-drawing", "image-svg+xml", "model"],
    "audio": ["audio-x-generic"],
    "video": ["video-x-generic"],
    "texto": ["text-x-generic", "text-x-preview", "text-markdown", "application-x-generic", "inode-symlink"],
    "codigo": ["text-x-script", "text-html", "text-css", "application-javascript", "application-json",
               "application-xml", "text-x-python", "text-x-csrc", "text-x-chdr", "text-x-c++src", "text-x-java",
               "text-rust", "text-x-go", "application-x-shellscript", "text-x-makefile"],
    "compactado": ["package-x-generic", "application-zip", "application-x-compressed-tar", "application-x-7z-compressed",
                   "application-x-rar", "application-x-xz", "application-gzip", "application-x-rpm",
                   "application-vnd.flatpak", "application-vnd.flatpak.ref", "x-package-repository"],
    "executavel": ["application-x-executable", "application-x-sharedlib", "application-x-addon",
                   "application-x-firmware", "application-x-msdownload", "application-x-appimage"],
}


# ── Mapa de apps ──────────────────────────────────────────────────────────
# (rótulo, seções, fonte, ids .desktop, nomes extras de ícone)
# O nome do arquivo SVG vem do Icon= lido no .desktop instalado; "extras" são
# nomes reais vistos no sistema que o app também usa (ex.: ícone de janela).
# A origem especial "os-release:LOGO" lê o LOGO= de /etc/os-release.
APPS = [
    # Dock
    # Fedora (LOGO= do os-release) fica de fora: usa o logo original do sistema, sem tile.
    ("Arquivos", ["Dock"], "desenho:arquivos", ["org.gnome.Nautilus.desktop"], []),
    ("Brave", ["Dock"], "simple:brave", ["brave-origin.desktop"], []),
    ("Spotify", ["Dock"], "original", ["spotify.desktop"], []),
    ("Deezer", ["Dock"], "simple:deezer", ["dev.aunetx.deezer.desktop", "deezer-desktop.desktop"], []),
    ("VS Code", ["Dock"], "original", ["com.microsoft.VSCode.desktop"], []),
    ("Claude", ["Dock"], "simple:claude", ["claude-desktop-unofficial.desktop"], ["claude-desktop"]),
    ("Karere", ["Dock"], "simple:whatsapp", ["io.github.tobagin.karere.desktop"], []),
    ("Discord", ["Dock"], "simple:discord", ["discord.desktop"], []),
    ("Thunderbird", ["Dock"], "original", ["net.thunderbird.Thunderbird.desktop"], []),
    ("Terminal", ["Dock"], "desenho:terminal", ["org.gnome.Ptyxis.desktop"], []),
    ("Editor de texto", ["Dock"], "desenho:editor", ["org.gnome.TextEditor.desktop"], []),
    ("LibreOffice Writer", ["Dock", "Escritório"], "original", ["libreoffice-writer.desktop"], []),
    ("Calculadora", ["Dock"], "desenho:calculadora", ["org.gnome.Calculator.desktop"], []),
    ("Calendário", ["Dock"], "desenho:calendario", ["org.gnome.Calendar.desktop"], []),

    # Grade
    ("Configurações", ["Grade"], "desenho:configuracoes", ["org.gnome.Settings.desktop"], []),
    ("Programas", ["Grade"], "desenho:programas", ["org.gnome.Software.desktop"], []),
    ("Ajustes", ["Grade"], "desenho:ajustes", ["org.gnome.tweaks.desktop"], []),
    ("Gerenciador de extensões", ["Grade"], "original", ["com.mattjakeman.ExtensionManager.desktop"], []),
    ("Extensões", ["Grade"], "desenho:extensoes",
     ["org.gnome.Extensions.desktop", "org.gnome.Shell.Extensions.desktop"], []),
    ("Firefox", ["Grade"], "original", ["org.mozilla.firefox.desktop"], []),
    ("Vivaldi", ["Grade"], "simple:vivaldi", ["vivaldi-stable.desktop"], []),
    ("btop++", ["Grade"], "original", ["btop.desktop"], []),
    ("YTMDesktop", ["Grade"], "original", ["app.ytmdesktop.ytmdesktop.desktop"], []),
    ("Audacious", ["Grade"], "original", ["audacious.desktop"], []),
    ("Reprodutor de vídeo", ["Grade", "Utilitários"], "desenho:video", ["org.gnome.Showtime.desktop"], []),
    ("AB Download Manager", ["Grade"], "original-sem-fundo",
     ["com.abdownloadmanager.abdownloadmanager.desktop"], []),
    ("LocalSend", ["Grade"], "original", ["org.localsend.localsend_app.desktop"], []),
    ("Solanum", ["Grade"], "original", ["org.gnome.Solanum.desktop"], []),
    ("Spruce", ["Grade"], "original", ["io.github.shonubot.Spruce.desktop"], []),
    ("OpenLogi", ["Grade"], "original-sem-fundo", ["openlogi.desktop"], []),
    ("D-Spy", ["Grade"], "original", ["org.gnome.dspy.desktop"], []),
    ("Flameshot", ["Grade"], "original", ["org.flameshot.Flameshot.desktop"], []),
    ("WhatsApp Web", ["Grade"], "simple:whatsapp",
     ["brave-hnpfjngllnobngcgfapefoaidbinmjnm-Default.desktop"], []),

    # Pasta Sistema
    ("Analisador de disco", ["Sistema"], "desenho:baobab", ["org.gnome.baobab.desktop"], []),
    ("Discos", ["Sistema"], "desenho:discos", ["org.gnome.DiskUtility.desktop"], []),
    ("Logs", ["Sistema"], "desenho:logs", ["org.gnome.Logs.desktop"], []),
    ("Controle parental", ["Sistema"], "desenho:controle-parental",
     ["org.freedesktop.MalcontentControl.desktop"], []),
    ("Monitor do sistema", ["Sistema"], "desenho:monitor-sistema",
     ["org.gnome.SystemMonitor.desktop", "gnome-system-monitor-kde.desktop"], []),

    # Pasta Utilitários
    ("Reprodutor de áudio", ["Utilitários"], "desenho:decibels", ["org.gnome.Decibels.desktop"], []),
    ("Conexões", ["Utilitários"], "desenho:conexoes", ["org.gnome.Connections.desktop"], []),
    ("Visualizador de documentos", ["Utilitários"], "desenho:papers", ["org.gnome.Papers.desktop"], []),
    ("Fontes", ["Utilitários"], "desenho:fontes", ["org.gnome.font-viewer.desktop"], []),
    ("Visualizador de imagens", ["Utilitários"], "desenho:imagens", ["org.gnome.Loupe.desktop"], []),
    ("Contatos", ["Utilitários"], "desenho:contatos", ["org.gnome.Contacts.desktop"], []),
    ("Relógios", ["Utilitários"], "desenho:relogios", ["org.gnome.clocks.desktop"], []),
    ("Clima", ["Utilitários"], "desenho:clima", ["org.gnome.Weather.desktop"], []),
    ("Mapas", ["Utilitários"], "desenho:mapas", ["org.gnome.Maps.desktop"], []),
    ("Digitalizador", ["Utilitários"], "desenho:scanner", ["org.gnome.SimpleScan.desktop"], []),
    ("Boxes", ["Utilitários"], "desenho:boxes", ["org.gnome.Boxes.desktop"], []),
    ("Câmera", ["Utilitários"], "desenho:camera", ["org.gnome.Snapshot.desktop"], []),
    ("Caracteres", ["Utilitários"], "desenho:caracteres", ["org.gnome.Characters.desktop"], []),
    ("Fedora Media Writer", ["Utilitários"], "original", ["org.fedoraproject.MediaWriter.desktop"], []),
    ("Tour", ["Utilitários"], "desenho:tour", ["org.gnome.Tour.desktop"], []),
    ("Ajuda", ["Utilitários"], "desenho:ajuda", ["org.gnome.Yelp.desktop"], []),

    # Pasta Escritório
    ("LibreOffice Calc", ["Escritório"], "original", ["libreoffice-calc.desktop"], []),
    ("LibreOffice Impress", ["Escritório"], "original", ["libreoffice-impress.desktop"], []),
    ("LibreOffice", ["Escritório"], "original", ["libreoffice-startcenter.desktop"], []),
    ("LibreOffice Draw", ["Escritório"], "original", ["libreoffice-draw.desktop", "icone:libreoffice-draw"], []),
    ("LibreOffice Math", ["Escritório"], "original", ["libreoffice-math.desktop", "icone:libreoffice-math"], []),
    ("LibreOffice Base", ["Escritório"], "original", ["libreoffice-base.desktop", "icone:libreoffice-base"], []),

    # Outros apps visíveis
    ("VLC", ["Outros apps"], "original", ["vlc.desktop"], []),
]


# ── Ícones fixos (não vêm de .desktop) ────────────────────────────────────
# (rótulo, seção, fonte, nomes de ícone, contexto/pasta em scalable/)
# Nomes iguais aos do Adwaita, para substituí-lo onde o GNOME os usa.
ICONES_FIXOS = [
    ("Pasta", "Pastas", "solto:pasta", ["folder", "inode-directory"], "places"),
    ("Pasta aberta", "Pastas", "solto:pasta-aberta", ["folder-open", "folder-drag-accept"], "places"),
    ("Documentos", "Pastas", "solto:pasta-documentos", ["folder-documents"], "places"),
    ("Downloads", "Pastas", "solto:pasta-downloads", ["folder-download"], "places"),
    ("Imagens", "Pastas", "solto:pasta-imagens", ["folder-pictures"], "places"),
    ("Músicas", "Pastas", "solto:pasta-musica", ["folder-music"], "places"),
    ("Vídeos", "Pastas", "solto:pasta-videos", ["folder-videos"], "places"),
    ("Modelos", "Pastas", "solto:pasta-modelos", ["folder-templates"], "places"),
    ("Público", "Pastas", "solto:pasta-publica", ["folder-publicshare"], "places"),
    ("Pasta remota", "Pastas", "solto:pasta-remota", ["folder-remote"], "places"),
    ("Projetos", "Pastas", "solto:pasta-projetos", ["folder-projects"], "places"),
    ("Pasta pessoal", "Pastas", "solto:pasta-pessoal", ["user-home"], "places"),
    ("Área de trabalho", "Pastas", "solto:pasta-area-de-trabalho", ["user-desktop"], "places"),
    ("Favoritos", "Lugares", "desenho:favoritos", ["user-bookmarks"], "places"),
    ("Servidor", "Lugares", "desenho:servidor", ["network-server"], "places"),
    ("Rede", "Lugares", "desenho:rede", ["network-workgroup"], "places"),
    ("Lixeira", "Lugares", "lixeira:lixeira", ["user-trash"], "places"),
    ("Lixeira cheia", "Lugares", "lixeira:lixeira-cheia", ["user-trash-full"], "places"),

    ("Fones", "Dispositivos", "desenho:fones", ["audio-headphones"], "devices"),
    ("Headset", "Dispositivos", "desenho:headset", ["audio-headset"], "devices"),
    ("Webcam", "Dispositivos", "desenho:webcam", ["camera-web"], "devices"),
    ("Computador", "Dispositivos", "desenho:computador", ["computer"], "devices"),
    ("Disco rígido", "Dispositivos", "desenho:disco", ["drive-harddisk"], "devices"),
    ("Vários discos", "Dispositivos", "desenho:multidisco", ["drive-multidisk"], "devices"),
    ("Drive óptico", "Dispositivos", "desenho:drive-optico", ["drive-optical"], "devices"),
    ("Mídia removível", "Dispositivos", "desenho:pendrive", ["drive-removable-media", "media-removable"], "devices"),
    ("Leitor de e-book", "Dispositivos", "desenho:leitor-ebook", ["ebook-reader"], "devices"),
    ("Controle de jogo", "Dispositivos", "desenho:controle", ["input-gaming"], "devices"),
    ("Teclado", "Dispositivos", "desenho:teclado", ["input-keyboard"], "devices"),
    ("Mouse", "Dispositivos", "desenho:mouse", ["input-mouse"], "devices"),
    ("Mesa digitalizadora", "Dispositivos", "desenho:mesa-digitalizadora", ["input-tablet"], "devices"),
    ("Cartão de memória", "Dispositivos", "desenho:cartao-sd", ["media-flash"], "devices"),
    ("CD/DVD", "Dispositivos", "desenho:cd", ["media-optical"], "devices"),
    ("Microfone", "Dispositivos", "desenho:microfone", ["microphone"], "devices"),
    ("Celular", "Dispositivos", "desenho:celular", ["phone"], "devices"),
    ("Impressora", "Dispositivos", "desenho:impressora", ["printer"], "devices"),
    ("Impressora de rede", "Dispositivos", "desenho:impressora-rede", ["printer-network"], "devices"),
    ("Scanner", "Dispositivos", "desenho:scanner", ["scanner"], "devices"),
    ("Monitor", "Dispositivos", "desenho:monitor", ["video-display"], "devices"),
]
