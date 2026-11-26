# [IA] Claude - testes dos comandos da Parte 1 no terminal (--alg, --fonte-consumivel, --armadilhas, --interactive, --out)
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_MAPAS = PASTA_PROJETO / "data" / "mapas"


def executar_cli(*argumentos):
    # NAO_ABRIR_NAVEGADOR: o --interactive so gera a pagina, sem abrir o navegador nos testes
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *argumentos],
        cwd=PASTA_PROJETO,
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "NAO_ABRIR_NAVEGADOR": "1"},
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
    ["--interactive", "--alg", "BFS"],
    ["--interactive", "--dataset", "dados"],
    ["--interactive", "--mapa", "nao_existe.txt"],
    ["--mapa", "mapa.txt", "--validar-mapa", "--out", "pasta"],
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
    assert "--interactive" in resultado.stdout


def test_pagina_interativa_tem_os_mapas_e_os_algoritmos(tmp_path):
    from src.solve import gerar_pagina_interativa
    destino = gerar_pagina_interativa(tmp_path / "pagina.html")
    html = destino.read_text(encoding="utf-8")
    assert "/*DADOS*/" not in html
    assert '"m01"' in html and '"m08"' in html
    assert "BELLMAN_FORD_FONTE_CONSUMIVEL" in html
    assert "<script src=" not in html   # tudo dentro de um arquivo so


# ---------------------------------------------------------------- --out (comandos do enunciado)

def test_comandos_do_enunciado_gravam_na_pasta_do_out(tmp_path):
    comandos = [
        ("m03_tres_chaves.txt", "--alg", "BFS"),
        ("m03_tres_chaves.txt", "--alg", "DIJKSTRA"),
        ("m05_bonus.txt", "--alg", "BELLMAN_FORD"),
        ("m06_fonte.txt", "--alg", "BELLMAN_FORD", "--fonte-consumivel"),
        ("m04_esteiras.txt", "--armadilhas"),
    ]
    for nome, *opcoes in comandos:
        resultado = executar_cli("--mapa", mapa(nome), *opcoes, "--out", str(tmp_path) + "/")
        assert resultado.returncode == 0, resultado.stderr

    bfs = json.loads((tmp_path / "m03_bfs.json").read_text(encoding="utf-8"))
    assert bfs["status"] == "OK" and bfs["passos"] == 87
    assert json.loads((tmp_path / "m03_dijkstra.json").read_text(encoding="utf-8"))["custo"] == 99
    assert json.loads((tmp_path / "m05_bellman_ford.json").read_text(encoding="utf-8"))["custo"] == 5
    fonte = json.loads((tmp_path / "m06_bellman_ford_fonte_consumivel.json").read_text(encoding="utf-8"))
    assert fonte["status"] == "OK" and fonte["custo"] == 10
    # o CSV sai igual ao que o solve.py gera em out/parte1
    gerado = (tmp_path / "armadilhas_m04.csv").read_bytes()
    assert gerado == (PASTA_PROJETO / "out" / "parte1" / "armadilhas_m04.csv").read_bytes()


def test_out_nao_pode_ser_um_arquivo(tmp_path):
    arquivo = tmp_path / "arquivo.txt"
    arquivo.write_text("x", encoding="utf-8")
    resultado = executar_cli("--mapa", mapa("m03_tres_chaves.txt"), "--alg", "BFS", "--out", str(arquivo))
    assert resultado.returncode == 2
    assert "--out deve ser uma pasta" in resultado.stderr


def test_interactive_com_mapa_e_out_gera_a_pagina_nesse_mapa(tmp_path):
    resultado = executar_cli("--mapa", mapa("m03_tres_chaves.txt"), "--interactive", "--out", str(tmp_path) + "/")
    assert resultado.returncode == 0, resultado.stderr
    html = (tmp_path / "labirinto_interativo.html").read_text(encoding="utf-8")
    assert 'window.MAPA_INICIAL = "m03";' in html
    assert '"g02"' in html


def test_interactive_com_mapa_novo_coloca_o_mapa_na_pagina(tmp_path):
    novo = tmp_path / "teste_professora.txt"
    novo.write_text("#######\n#S..G.#\n#######\n", encoding="utf-8")
    resultado = executar_cli("--mapa", str(novo), "--interactive", "--out", str(tmp_path / "pagina.html"))
    assert resultado.returncode == 0, resultado.stderr
    html = (tmp_path / "pagina.html").read_text(encoding="utf-8")
    assert 'window.MAPA_INICIAL = "teste";' in html
    assert '"teste": {"id": "teste", "nome": "Professora"' in html


def test_interactive_avisa_quando_o_navegador_nao_abre(tmp_path, monkeypatch, capsys):
    from src import cli
    monkeypatch.delenv("NAO_ABRIR_NAVEGADOR", raising=False)
    monkeypatch.setattr(cli.webbrowser, "open", lambda url: False)
    with pytest.raises(SystemExit) as saida:
        cli.main(["--mapa", mapa("m02_uma_chave.txt"), "--interactive", "--out", str(tmp_path)])
    assert saida.value.code == 1
    assert "nao foi possivel abrir o navegador" in capsys.readouterr().err
