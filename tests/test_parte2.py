# [IA] Claude - testes dos comandos da Parte 2 com um dataset pequeno montado a mao
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.graphs.io import ler_dataset, montar_grafo_dataset
from src.parte2 import (
    executar_algoritmo,
    grafo_com_pesos_dijkstra,
    localizar_arquivo_dataset,
    montar_recorte,
)


PASTA_PROJETO = Path(__file__).resolve().parents[1]

# 1 -> 2 (amigo), 2 -> 3 (inimigo), 1 -> 3 (amigo), 3 -> 1 (amigo): a partir de 1 nao ha ciclo negativo
#   (1 -> 2 -> 3 -> 1 custa +1 e 1 -> 3 -> 1 custa +2)
# 6 -> 4 (amigo), 4 -> 5 e 5 -> 4 (inimigos mutuos): ciclo negativo 4 -> 5 -> 4, custo -2
LINHAS = ["1\t2\t1", "2\t3\t-1", "1\t3\t1", "3\t1\t1", "6\t4\t1", "4\t5\t-1", "5\t4\t-1"]


@pytest.fixture
def pasta_dataset(tmp_path):
    pasta = tmp_path / "dataset"
    pasta.mkdir()
    (pasta / "pequeno.txt").write_text("# comentario\n" + "\n".join(LINHAS) + "\n", encoding="utf-8")
    return pasta


@pytest.fixture
def grafo(pasta_dataset):
    return montar_grafo_dataset(ler_dataset(pasta_dataset / "pequeno.txt"))


def executar_cli(*argumentos):
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *map(str, argumentos)],
        cwd=PASTA_PROJETO,
        capture_output=True,
        text=True,
        timeout=60,
    )


# ---------------------------------------------------------------- leitura

def test_localiza_dataset_pela_pasta_ou_pelo_arquivo(pasta_dataset):
    arquivo = pasta_dataset / "pequeno.txt"
    assert localizar_arquivo_dataset(pasta_dataset) == arquivo
    assert localizar_arquivo_dataset(arquivo) == arquivo


def test_pasta_sem_dataset_gera_erro(tmp_path):
    with pytest.raises(FileNotFoundError, match="Nenhum arquivo"):
        localizar_arquivo_dataset(tmp_path)


def test_pasta_com_dois_datasets_gera_erro(pasta_dataset):
    (pasta_dataset / "outro.txt").write_text("1\t2\t1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mais de um dataset"):
        localizar_arquivo_dataset(pasta_dataset)


# ---------------------------------------------------------------- grafos

def test_pesos_do_dijkstra_trocam_amigo_por_1_e_inimigo_por_2(grafo):
    novo = grafo_com_pesos_dijkstra(grafo)
    pesos = {(u, v): peso for u in novo.nos() for v, peso, _, _ in novo.vizinhos(u)}
    assert pesos[(1, 2)] == 1
    assert pesos[(2, 3)] == 2
    assert pesos[(4, 5)] == 2
    assert novo.tamanho() == grafo.tamanho()
    assert not novo.tem_peso_neg


def test_recortes_sao_reprodutiveis_e_o_de_100_preserva_o_grafo(grafo):
    assert montar_recorte(grafo, 100).tamanho() == grafo.tamanho()
    assert set(montar_recorte(grafo, 50).nos()) == set(montar_recorte(grafo, 50).nos())
    assert set(montar_recorte(grafo, 10).nos()) <= set(montar_recorte(grafo, 50).nos())


# ---------------------------------------------------------------- algoritmos

def test_bfs_encontra_menor_numero_de_passos(grafo):
    resultado = executar_algoritmo(grafo, "BFS", 1, 3)
    assert resultado["status"] == "OK"
    assert resultado["caminho"] == [1, 3]
    assert resultado["passos"] == 1


def test_dijkstra_e_bellman_ford_escolhem_caminhos_diferentes(grafo):
    # Dijkstra (amigo 1, inimigo 2): 1 -> 3 custa 1 e 1 -> 2 -> 3 custa 3
    dijkstra = executar_algoritmo(grafo, "DIJKSTRA", 1, 3)
    assert dijkstra["caminho"] == [1, 3]
    assert dijkstra["custo"] == 1
    # Bellman-Ford (sinais): 1 -> 2 -> 3 custa 0 e 1 -> 3 custa 1
    bellman_ford = executar_algoritmo(grafo, "BELLMAN_FORD", 1, 3)
    assert bellman_ford["status"] == "OK"
    assert bellman_ford["caminho"] == [1, 2, 3]
    assert bellman_ford["custo"] == 0


def test_bellman_ford_detecta_e_mostra_ciclo_negativo(grafo):
    resultado = executar_algoritmo(grafo, "BELLMAN_FORD", 6)
    assert resultado["status"] == "CICLO_NEGATIVO"
    ciclo = resultado["ciclo_negativo"]
    assert ciclo[0] == ciclo[-1]
    assert set(ciclo) == {4, 5}
    assert resultado["custo_ciclo"] == -2
    assert resultado["caminho_ate_ciclo"] == [6, 4]


def test_dfs_classifica_arcos_e_indica_ciclo(grafo):
    resultado = executar_algoritmo(grafo, "DFS", 1)
    assert resultado["tem_ciclo"] is True
    assert sum(resultado["arcos_por_tipo"].values()) == 4  # arcos que saem de 1, 2 e 3
    assert resultado["arcos_por_tipo"]["retorno"] >= 1
    assert resultado["alcancados"] == 3


def test_destino_inalcancavel_tem_status_sem_solucao(grafo):
    resultado = executar_algoritmo(grafo, "BFS", 1, 6)
    assert resultado["status"] == "SEM_SOLUCAO"
    assert "caminho" not in resultado


def test_usuario_inexistente_gera_erro(grafo):
    with pytest.raises(KeyError):
        executar_algoritmo(grafo, "BFS", 99)


# ---------------------------------------------------------------- linha de comando

def test_cli_roda_dijkstra_e_salva_o_resultado(pasta_dataset, tmp_path):
    saida = tmp_path / "saida"
    resultado = executar_cli("--dataset", pasta_dataset, "--alg", "dijkstra", "--source", 1, "--target", 3,
                             "--out", saida)
    assert resultado.returncode == 0, resultado.stderr
    assert "Status: OK" in resultado.stdout
    assert "Caminho: 1 -> 3" in resultado.stdout
    salvo = json.loads((saida / "cli_pequeno_dijkstra_1_3.json").read_text(encoding="utf-8"))
    assert salvo["custo"] == 1
    assert salvo["recorte_percentual"] == 100


def test_cli_bellman_ford_mostra_o_ciclo_negativo(pasta_dataset, tmp_path):
    resultado = executar_cli("--dataset", pasta_dataset, "--alg", "BELLMAN_FORD", "--source", 6,
                             "--out", tmp_path)
    assert resultado.returncode == 0, resultado.stderr
    assert "Status: CICLO_NEGATIVO" in resultado.stdout
    assert "(custo -2)" in resultado.stdout


@pytest.mark.parametrize("argumentos", [
    [],                                              # sem --alg nem --benchmark
    ["--alg", "BFS"],                                # sem --source
    ["--alg", "BFS", "--source", 99],                # usuario inexistente
    ["--alg", "XYZ", "--source", 1],                 # algoritmo desconhecido
    ["--benchmark", "--alg", "BFS"],                 # combinacao invalida
    ["--validar-mapa"],                              # opcao da Parte 1
    ["--benchmark"],                                 # dataset pequeno demais para o benchmark
])
def test_cli_recusa_argumentos_incorretos(pasta_dataset, tmp_path, argumentos):
    resultado = executar_cli("--dataset", pasta_dataset, "--out", tmp_path, *argumentos)
    assert resultado.returncode == 2
    assert resultado.stderr
    assert "Traceback" not in resultado.stderr


def test_cli_recusa_mapa_e_dataset_juntos(pasta_dataset):
    resultado = executar_cli("--mapa", "data/mapas/m01_terreno.txt", "--dataset", pasta_dataset)
    assert resultado.returncode == 2
    assert "Traceback" not in resultado.stderr


# [IA] Claude – regressoes do checklist da Parte 2 (destino com ciclo negativo, .gz cortado e --out invalido)

def test_bellman_ford_com_ciclo_e_destino_inalcancavel_da_sem_solucao(grafo):
    # a partir de 6 ha o ciclo 4 -> 5 -> 4, mas nenhum caminho chega ao usuario 1
    resultado = executar_algoritmo(grafo, "BELLMAN_FORD", 6, 1)
    assert resultado["status"] == "SEM_SOLUCAO"
    assert "ciclo_negativo" not in resultado


def test_bellman_ford_com_ciclo_e_destino_alcancavel_nao_calcula_o_custo(grafo):
    resultado = executar_algoritmo(grafo, "BELLMAN_FORD", 6, 5)
    assert resultado["status"] == "CICLO_NEGATIVO"
    assert resultado["custo_calculado"] is False
    assert "custo" not in resultado


def test_cli_bellman_ford_destino_inalcancavel(pasta_dataset, tmp_path):
    resultado = executar_cli("--dataset", pasta_dataset, "--alg", "BELLMAN_FORD", "--source", 6, "--target", 1,
                             "--out", tmp_path)
    assert resultado.returncode == 0, resultado.stderr
    assert "Status: SEM_SOLUCAO" in resultado.stdout
    assert "Nao existe caminho de 6 ate 1." in resultado.stdout


def test_cli_bellman_ford_destino_alcancavel_avisa_que_o_custo_nao_foi_calculado(pasta_dataset, tmp_path):
    resultado = executar_cli("--dataset", pasta_dataset, "--alg", "BELLMAN_FORD", "--source", 6, "--target", 5,
                             "--out", tmp_path)
    assert resultado.returncode == 0, resultado.stderr
    assert "Status: CICLO_NEGATIVO" in resultado.stdout
    assert "o custo ate o destino nao foi calculado" in resultado.stdout


def test_cli_gz_cortado_mostra_mensagem_sem_traceback(tmp_path):
    import gzip
    linhas = "\n".join(f"{i}\t{i + 1}\t1" for i in range(20000)) + "\n"
    compactado = gzip.compress(linhas.encode("utf-8"))
    arquivo = tmp_path / "cortado.txt.gz"
    arquivo.write_bytes(compactado[: len(compactado) // 2])
    resultado = executar_cli("--dataset", arquivo, "--alg", "BFS", "--source", 1, "--out", tmp_path / "saida")
    assert resultado.returncode != 0
    assert "incompleto ou corrompido" in resultado.stderr
    assert "Traceback" not in resultado.stderr


def test_cli_out_apontando_para_arquivo_falha_antes_da_busca(pasta_dataset, tmp_path):
    arquivo = tmp_path / "nao_e_pasta.txt"
    arquivo.write_text("x", encoding="utf-8")
    resultado = executar_cli("--dataset", pasta_dataset, "--alg", "BFS", "--source", 1, "--out", arquivo)
    assert resultado.returncode != 0
    assert "Status:" not in resultado.stdout
    assert "Traceback" not in resultado.stderr


def test_cli_falha_ao_gravar_encerra_com_erro(pasta_dataset, tmp_path):
    # uma pasta dentro de um arquivo nao pode ser criada: a gravacao falha depois da busca
    arquivo = tmp_path / "arquivo.txt"
    arquivo.write_text("x", encoding="utf-8")
    resultado = executar_cli("--dataset", pasta_dataset, "--alg", "BFS", "--source", 1, "--out", arquivo / "sub")
    assert resultado.returncode == 1
    assert "nao foi possivel salvar" in resultado.stderr
    assert "Resultado salvo" not in resultado.stdout
    assert "Traceback" not in resultado.stderr
