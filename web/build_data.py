# [IA] Claude Code – script que gera web/data.js (apoio com IO)
"""Gera web/data.js com os dados do site.

Os dados vem de src/pagina_site.py, que calcula a Parte 1 com as funcoes do src/solve.py
(entram todos os mapas: m01 a m08, g01 e g02) e le o resumo da Parte 2 em out/parte2.

Uso (na raiz do projeto):
    python web/build_data.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import os  # noqa: E402

os.chdir(RAIZ)   # os caminhos do projeto (data/, out/, web/) sao relativos a raiz

from src.pagina_site import gerar_data_js  # noqa: E402


def main():
    destino = gerar_data_js()
    print(f"{destino} gerado ({destino.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
