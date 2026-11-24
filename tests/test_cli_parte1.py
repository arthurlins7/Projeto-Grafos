# [IA] Claude - testes dos comandos da Parte 1 no terminal (--alg, --fonte-consumivel, --armadilhas)
import subprocess
import sys
from pathlib import Path

import pytest


PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_MAPAS = PASTA_PROJETO / "data" / "mapas"


def executar_cli(*argumentos):
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *argumentos],
        cwd=PASTA_PROJETO,
        capture_output=True,
        text=True,
        timeout=120,
    )


def mapa(nome):
    return str(PASTA_MAPAS / nome)


def test_bfs_e_dijkstra_no_m01_dao_caminhos_diferentes():
    bfs = executar_cli("--mapa", mapa("m01_terreno.txt"), "--alg", "BFS")
    dijkstra = executar_cli("--mapa", mapa("m01_terreno.txt"), "--alg", "DIJKSTRA")
    assert bfs.returncode == 0 and dijkstra.returncode == 0
    assert "Passos: 10 | custo: 30" in bfs.stdout
    assert "Passos: 14 | custo: 20" in dijkstra.stdout


def test_dijkstra_recusa_peso_negativo_no_m05():
    resultado = executar_cli("--mapa", mapa("m05_bonus.txt"), "--alg", "dijkstra")
    assert resultado.returncode == 0
    assert "Status: RECUSA" in resultado.stdout
    assert "peso -4" in resultado.stdout


def test_bellman_ford_no_m05_pega_os_bonus():
    resultado = executar_cli("--mapa", mapa("m05_bonus.txt"), "--alg", "BELLMAN_FORD")
    assert "Passos: 20 | custo: 5" in resultado.stdout


def test_fonte_consumivel_tira_o_ciclo_negativo_do_m06():
    sem = executar_cli("--mapa", mapa("m06_fonte.txt"), "--alg", "BELLMAN_FORD")
    com = executar_cli("--mapa", mapa("m06_fonte.txt"), "--alg", "BELLMAN_FORD", "--fonte-consumivel")
    assert "Status: CICLO_NEGATIVO" in sem.stdout
    assert "(custo -1)" in sem.stdout
    assert "Status: OK" in com.stdout
    assert "Passos: 10 | custo: 10" in com.stdout


def test_m07_sem_solucao_e_todos_os_estados_sao_armadilha():
    resultado = executar_cli("--mapa", mapa("m07_impossivel.txt"), "--alg", "BFS", "--armadilhas")
    assert "Status: SEM_SOLUCAO" in resultado.stdout
    assert "estados-armadilha: 16 de 16" in resultado.stdout


def test_armadilhas_do_m04():
    resultado = executar_cli("--mapa", mapa("m04_esteiras.txt"), "--armadilhas")
    assert resultado.returncode == 0
    assert "estados-armadilha: 4 de 37" in resultado.stdout
    assert "(1,3)|-|{}" in resultado.stdout


def test_dfs_mostra_os_tipos_de_arco():
    resultado = executar_cli("--mapa", mapa("m02_uma_chave.txt"), "--alg", "DFS")
    assert "arvore=38" in resultado.stdout
    assert "Tem ciclo: sim" in resultado.stdout


@pytest.mark.parametrize("argumentos", [
    ["--mapa", "mapa.txt", "--fonte-consumivel"],
    ["--mapa", "mapa.txt", "--validar-mapa", "--armadilhas"],
    ["--mapa", "mapa.txt", "--validar-mapa", "--fonte-consumivel"],
    ["--mapa", "mapa.txt", "--alg", "BFS", "--source", "1"],
    ["--dataset", "dados", "--armadilhas"],
    ["--dataset", "dados", "--alg", "BFS", "--source", "1", "--fonte-consumivel"],
])
def test_recusa_combinacoes_invalidas(argumentos):
    resultado = executar_cli(*argumentos)
    assert resultado.returncode == 2
    assert resultado.stdout == ""
    assert "Traceback" not in resultado.stderr


def test_ajuda_mostra_as_opcoes_da_parte1():
    resultado = executar_cli("--help")
    assert "--fonte-consumivel" in resultado.stdout
    assert "--armadilhas" in resultado.stdout