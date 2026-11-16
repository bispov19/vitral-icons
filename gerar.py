#!/usr/bin/env python3
"""Atalho: o gerador do Vitral-icons (escuro e claro) mora em icons/gerar.py.

O serviço do systemd (vitral-icons.service) chama este caminho.
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "icons" / "gerar.py"), run_name="__main__")
