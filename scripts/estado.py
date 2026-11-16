#!/usr/bin/env python3
"""Backup e restauração do que o apply.sh muda (usado por apply.sh e revert.sh).

    estado.py chave <schema> <chave>     guarda o valor atual do gsettings (só da 1ª vez)
    estado.py arquivo <caminho>          guarda uma cópia do arquivo (ou que ele não existia)
    estado.py marca <nome>               registra uma ação extra (ex.: flatpak-override)
    estado.py restaurar [--dry-run]      desfaz tudo e arquiva o backup.json
    estado.py mostrar                    imprime o backup

O backup fica em ~/.config/brisa/backup.json. Cada valor é guardado só na
primeira vez em que é mudado, então rodar o apply.sh de novo não perde o
estado original.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
PASTA = CONFIG / "brisa"
BACKUP = PASTA / "backup.json"
COPIAS = PASTA / "backup"


def ler():
    if BACKUP.exists():
        return json.loads(BACKUP.read_text())
    return {"criado": time.strftime("%Y-%m-%d %H:%M:%S"), "gsettings": {}, "arquivos": {}, "marcas": []}


def gravar(dados):
    PASTA.mkdir(parents=True, exist_ok=True)
    BACKUP.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n")


def gsettings(*args):
    return subprocess.run(["gsettings", *args], capture_output=True, text=True, check=True).stdout.strip()


def chave(schema, nome):
    dados = ler()
    id_ = f"{schema} {nome}"
    if id_ not in dados["gsettings"]:
        dados["gsettings"][id_] = gsettings("get", schema, nome)
        gravar(dados)


def arquivo(caminho):
    dados = ler()
    caminho = str(Path(caminho).expanduser())
    if caminho in dados["arquivos"]:
        return
    p = Path(caminho)
    registro = {"existia": p.exists() or p.is_symlink(), "copia": None}
    if registro["existia"]:
        COPIAS.mkdir(parents=True, exist_ok=True)
        destino = COPIAS / (caminho.strip("/").replace("/", "__") + time.strftime(".%Y%m%d-%H%M%S"))
        shutil.copy2(p, destino, follow_symlinks=True)
        registro["copia"] = str(destino)
    dados["arquivos"][caminho] = registro
    gravar(dados)


def marca(nome):
    dados = ler()
    if nome not in dados["marcas"]:
        dados["marcas"].append(nome)
        gravar(dados)


def restaurar(seco):
    if not BACKUP.exists():
        print("Nada a reverter: não há ~/.config/brisa/backup.json.")
        return

    def fazer(descricao, acao):
        print(("  [dry-run] " if seco else "  ") + descricao)
        if not seco:
            acao()

    dados = ler()
    print(f"==> Restaurando o estado de {dados.get('criado', '?')}")
    for id_, valor in dados["gsettings"].items():
        schema, nome = id_.split(" ", 1)
        fazer(f"gsettings set {schema} {nome} {valor}", lambda s=schema, n=nome, v=valor: gsettings("set", s, n, v))
    for caminho, reg in dados["arquivos"].items():
        if reg["existia"]:
            fazer(f"restaura {caminho} (de {reg['copia']})",
                  lambda c=caminho, r=reg: shutil.copy2(r["copia"], c))
        else:
            fazer(f"remove {caminho} (não existia antes)", lambda c=caminho: Path(c).unlink(missing_ok=True))
    # Ações na sessão real; com BRISA_TESTE=1 só são mostradas.
    teste = os.environ.get("BRISA_TESTE") == "1"
    extras = {
        "flatpak-override": ["flatpak", "override", "--user", "--nofilesystem=xdg-config/gtk-4.0",
                             "--nofilesystem=xdg-config/gtk-3.0"],
        "habilitou-user-theme": ["gnome-extensions", "disable",
                                 "user-theme@gnome-shell-extensions.gcampax.github.com"],
    }
    for nome, cmd in extras.items():
        if nome in dados["marcas"]:
            if teste:
                print("  [teste] " + " ".join(cmd))
            else:
                fazer(" ".join(cmd), lambda c=cmd: subprocess.run(c, check=True))
    arquivado = BACKUP.with_name(f"backup.restaurado-{time.strftime('%Y%m%d-%H%M%S')}.json")
    fazer(f"arquiva o backup em {arquivado}", lambda: BACKUP.rename(arquivado))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "chave":
        chave(*args)
    elif cmd == "arquivo":
        arquivo(*args)
    elif cmd == "marca":
        marca(*args)
    elif cmd == "restaurar":
        restaurar("--dry-run" in args)
    elif cmd == "mostrar":
        print(json.dumps(ler(), ensure_ascii=False, indent=1))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
