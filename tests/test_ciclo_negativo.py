# [IA] Claude - testes do Bellman-Ford ate o ALVO com ciclo negativo (mapas pequenos montados a mao)
import subprocess
import sys
from pathlib import Path

from src.graphs.io import ler_mapa
from src.solve import gabarito_do_mapa, percurso_menor_custo, resolver_mapa


PASTA_PROJETO = Path(__file__).resolve().parents[1]

# fontes (*) espalhadas: o ciclo negativo fica no meio do caminho ate G
MAPA_CICLO_NA_ROTA = [
    "########",
    "#*~,...#",
    "#*.~*.*#",
    "#~...,~#",
    "#..,GS*#",
    "########",
]

# a esteira (v) leva pra um bolsao com fonte de onde nao da pra voltar:
# o ciclo existe, mas dele nao se chega em G, que fica a 3 passos do S
MAPA_CICLO_FORA_DA_ROTA = [
    "#######",
    "#S..G.#",
    "#v#####",
    "#*.####",
    "#######",
]


def test_ciclo_na_rota_e_detectado_pelo_bellman_ford():
    resultado = resolver_mapa(MAPA_CICLO_NA_ROTA, "BELLMAN_FORD")
    assert resultado["status"] == "CICLO_NEGATIVO"
    assert resultado["ciclo"][0] == resultado["ciclo"][-1]
    assert resultado["custo_ciclo"] < 0


def test_percurso_com_ciclo_na_rota_nao_trava():
    # antes a funcao ficava presa dando voltas no ciclo; roda em outro processo com tempo limite
    codigo = (
        "from src.solve import gabarito_do_mapa, percurso_menor_custo\n"
        f"linhas = {MAPA_CICLO_NA_ROTA!r}\n"
        "print(percurso_menor_custo(linhas))\n"
        "print(gabarito_do_mapa(linhas)['custo'])\n"
    )
    saida = subprocess.run([sys.executable, "-c", codigo], cwd=PASTA_PROJETO,
                           capture_output=True, text=True, timeout=60)
    assert saida.returncode == 0, saida.stderr
    assert saida.stdout.split() == ["None", "None"]


def test_ciclo_fora_da_rota_nao_esconde_o_custo_ate_a_saida():
    resultado = resolver_mapa(MAPA_CICLO_FORA_DA_ROTA, "BELLMAN_FORD")
    assert resultado["status"] == "OK"
    assert resultado["passos"] == 3
    assert resultado["custo"] == 3
    assert resultado["custo_ciclo_fora_da_rota"] < 0


def test_ciclo_fora_da_rota_no_percurso_e_no_gabarito():
    percurso = percurso_menor_custo(MAPA_CICLO_FORA_DA_ROTA)
    assert percurso["algoritmo"] == "BELLMAN_FORD"
    assert percurso["custo_total"] == 3
    assert gabarito_do_mapa(MAPA_CICLO_FORA_DA_ROTA)["custo"] == 3


def test_m06_continua_com_ciclo_negativo():
    linhas = ler_mapa(PASTA_PROJETO / "data" / "mapas" / "m06_fonte.txt")
    assert resolver_mapa(linhas, "BELLMAN_FORD")["status"] == "CICLO_NEGATIVO"
    assert resolver_mapa(linhas, "BELLMAN_FORD", fonte_consumivel=True)["status"] == "OK"