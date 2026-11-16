#!/usr/bin/env python3
"""Atalho: o gerador de ícones mora em icons/gerar.py (o serviço systemd chama este caminho)."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "icons" / "gerar.py"), run_name="__main__")
