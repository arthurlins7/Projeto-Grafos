# [IA] Claude - orquestracao da Parte 2 pela linha de comando (leitura, recortes, execucao e benchmark)
"""Parte 2: algoritmos no grafo do Slashdot pela linha de comando.

Segue as mesmas escolhas do notebook 02_grafos_algoritmos.ipynb:
- recortes de 10%, 50% e 100% dos usuarios, embaralhados com a semente 42;
- BFS e DFS sem pesos (cada seta vale um passo);
- Dijkstra com pesos amigo 1 e inimigo 2 (ele nao aceita peso negativo);
- Bellman-Ford com os sinais originais (amigo +1, inimigo -1).
"""

import json
import random
import unicodedata
from pathlib import Path
from statistics import mean, median
from time import perf_counter

import pandas as pd

from src.graphs.algorithms import bellman_ford, bfs, custo_caminho, dfs, dijkstra, montar_caminho
from src.graphs.graph import GrafoDirigido
from src.graphs.io import montar_grafo_dataset


SEMENTE = 42
PERCENTUAIS = (10, 50, 100)
REPETICOES = 5
ALGORITMOS = ("BFS", "DFS", "DIJKSTRA", "BELLMAN_FORD")
PESO_DIJKSTRA = {1: 1, -1: 2}
TIPOS_DE_ARCO = ("arvore", "retorno", "avanco", "cruzamento")

# textos gravados no parte2_report.json (iguais aos do notebook)
SEM_PESOS = "sem pesos (cada seta é um passo)"
PESOS_DIJKSTRA = "amigo 1, inimigo 2"
SINAIS = "sinal original (amigo +1, inimigo -1)"

# textos do terminal ficam sem acentos para nao dar erro de codificacao no Windows
PESOS_NO_TERMINAL = {
    "BFS": "sem pesos (cada seta vale 1 passo)",
    "DFS": "sem pesos (cada seta vale 1 passo)",
    "DIJKSTRA": "amigo 1, inimigo 2",
    "BELLMAN_FORD": "sinal original (amigo +1, inimigo -1)",
}


def sem_acentos(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


# ---------------------------------------------------------------- leitura e grafos

def localizar_arquivo_dataset(caminho):
    """Aceita o arquivo do dataset ou a pasta que o contem."""
    caminho = Path(caminho)
    if caminho.is_file():
        return caminho
    if not caminho.is_dir():
        raise FileNotFoundError(f"Dataset nao encontrado: {caminho}")

    arquivos = sorted(
        p for p in caminho.iterdir()
        if p.is_file() and (p.name.endswith(".txt") or p.name.endswith(".txt.gz"))
    )
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo .txt ou .txt.gz na pasta {caminho}")
    if len(arquivos) > 1:
        nomes = ", ".join(p.name for p in arquivos)
        raise ValueError(f"A pasta {caminho} tem mais de um dataset ({nomes}); informe o arquivo.")
    return arquivos[0]


def nome_do_dataset(arquivo):
    # "soc-sign-Slashdot090221.txt.gz" -> "soc-sign-Slashdot090221"
    return Path(arquivo).name.removesuffix(".gz").removesuffix(".txt")


def montar_recorte(grafo, percentual, semente=SEMENTE):
    """Subgrafo induzido pelos primeiros `percentual`% dos usuarios embaralhados com a semente.

    Como todos os recortes usam o inicio da mesma lista, os menores ficam contidos nos maiores.
    """
    usuarios = sorted(grafo.nos())
    random.Random(semente).shuffle(usuarios)
    quantidade = grafo.ordem() * percentual // 100
    return grafo.subgrafo_induzido(usuarios[:quantidade])


def montar_recortes(grafo, percentuais=PERCENTUAIS, semente=SEMENTE):
    return {percentual: montar_recorte(grafo, percentual, semente) for percentual in percentuais}


def grafo_com_pesos_dijkstra(grafo):
    """Copia do grafo com amigo = 1 e inimigo = 2, mantendo arcos, direcao e ordem dos vizinhos."""
    novo = GrafoDirigido(grafo.nome + "_dijkstra")
    for usuario in grafo.nos():
        novo.adicionar_no(usuario)
    for origem in grafo.nos():
        for destino, sinal, _, _ in grafo.vizinhos(origem):
            novo.adicionar_arco(origem, destino, peso=PESO_DIJKSTRA[sinal])
    return novo


# ---------------------------------------------------------------- uma execucao

def caminho_ate_ciclo(grafo, origem, ciclo):
    """Menor caminho (BFS) da origem ate algum usuario do ciclo."""
    _, pai, _ = bfs(grafo, origem)
    caminhos = [montar_caminho(pai, usuario) for usuario in ciclo[:-1]]
    caminhos = [caminho for caminho in caminhos if caminho is not None]
    return min(caminhos, key=len) if caminhos else None


def executar_algoritmo(grafo, algoritmo, origem, destino=None):
    """Roda um algoritmo a partir de `origem` e devolve um resumo do resultado.

    O grafo deve ter os sinais originais; para o Dijkstra, os pesos viram amigo 1 e inimigo 2.
    Status possiveis: OK, SEM_SOLUCAO (destino inalcancavel) e CICLO_NEGATIVO (Bellman-Ford).
    """
    algoritmo = algoritmo.upper()
    if algoritmo not in ALGORITMOS:
        raise ValueError(f"Algoritmo desconhecido: {algoritmo}. Use um de: {', '.join(ALGORITMOS)}.")
    for papel, usuario in (("origem", origem), ("destino", destino)):
        if usuario is not None and not grafo.tem_no(usuario):
            raise KeyError(f"O usuario de {papel} {usuario} nao existe no grafo.")

    # a troca de pesos fica fora do cronometro: so o algoritmo e medido
    grafo_usado = grafo_com_pesos_dijkstra(grafo) if algoritmo == "DIJKSTRA" else grafo
    resultado = {
        "algoritmo": algoritmo,
        "pesos": PESOS_NO_TERMINAL[algoritmo],
        "origem": origem,
        "destino": destino,
    }

    ciclo = None
    custos = None
    inicio = perf_counter()
    if algoritmo == "BFS":
        _, pai, _ = bfs(grafo_usado, origem)
    elif algoritmo == "DFS":
        pai, _, classificacao, tem_ciclo = dfs(grafo_usado, origem)
    elif algoritmo == "DIJKSTRA":
        custos, pai, _ = dijkstra(grafo_usado, origem)
    else:
        custos, pai, ciclo = bellman_ford(grafo_usado, origem)
    resultado["tempo_ms"] = round((perf_counter() - inicio) * 1000, 4)

    if ciclo is not None:
        # [IA] Claude – com --target, a BFS confere se o destino e alcancavel antes de falar do ciclo
        if destino is not None:
            alcancaveis, _, _ = bfs(grafo, origem)
            if destino not in alcancaveis:
                resultado["status"] = "SEM_SOLUCAO"
                resultado["alcancados"] = len(alcancaveis)
                return resultado
            # o Bellman-Ford para no primeiro ciclo encontrado: o custo ate o destino fica sem calculo
            resultado["custo_calculado"] = False
        # com um ciclo negativo alcancavel, o menor custo deixa de existir
        resultado["status"] = "CICLO_NEGATIVO"
        resultado["ciclo_negativo"] = ciclo
        resultado["custo_ciclo"] = custo_caminho(grafo_usado, ciclo)
        resultado["caminho_ate_ciclo"] = caminho_ate_ciclo(grafo, origem, ciclo)
        return resultado

    resultado["alcancados"] = len(pai)
    if algoritmo == "DFS":
        contagem = {tipo: 0 for tipo in TIPOS_DE_ARCO}
        for _, _, tipo in classificacao:
            contagem[tipo] += 1
        resultado["arcos_por_tipo"] = contagem
        resultado["tem_ciclo"] = tem_ciclo

    if destino is None:
        resultado["status"] = "OK"
        return resultado

    caminho = montar_caminho(pai, destino)
    if caminho is None:
        resultado["status"] = "SEM_SOLUCAO"
        return resultado

    resultado["status"] = "OK"
    resultado["caminho"] = caminho
    resultado["passos"] = len(caminho) - 1
    if custos is not None:
        resultado["custo"] = custos[destino]
    return resultado


def salvar_resultado(resultado, pasta_saida, recorte=100):
    # [IA] Claude – o nome do dataset entra no arquivo para execucoes de datasets diferentes nao se sobrescreverem
    partes = ["cli"]
    if resultado.get("dataset"):
        partes.append(resultado["dataset"])
    partes += [resultado["algoritmo"].lower(), str(resultado["origem"])]
    nome = "_".join(partes)
    if resultado["destino"] is not None:
        nome += f"_{resultado['destino']}"
    if recorte != 100:
        nome += f"_recorte{recorte}"
    caminho = Path(pasta_saida) / f"{nome}.json"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(resultado, ensure_ascii=False, indent=2, default=int), encoding="utf-8")
    return caminho


# ---------------------------------------------------------------- benchmark

def medicao(algoritmo, tarefa, recorte, fonte, tempos, pesos, **detalhes):
    """Uma linha do parte2_report.json (mesmo formato do notebook)."""
    return {
        "algoritmo": algoritmo,
        "tarefa": tarefa,
        "recorte_percentual": int(recorte),
        "usuario_partida": int(fonte),
        "pesos": pesos,
        "execucoes": len(tempos),
        "tempo_medio_ms": round(mean(tempos), 4),
        "tempo_mediano_ms": round(median(tempos), 4),
        "tempos_ms": [round(t, 4) for t in tempos],
        **detalhes,
    }


def cronometrar(funcao, grafo, fonte):
    inicio = perf_counter()
    resultado = funcao(grafo, fonte)
    return resultado, (perf_counter() - inicio) * 1000


def medir_em_par(par, grafo, fonte, repeticoes=REPETICOES):
    """Mede dois algoritmos alternando a ordem a cada repeticao, como no notebook."""
    tempos = {nome: [] for nome, _ in par}
    resultados = {}
    for repeticao in range(repeticoes):
        ordem = par if repeticao % 2 == 0 else par[::-1]
        for nome, funcao in ordem:
            resultados[nome], tempo = cronometrar(funcao, grafo, fonte)
            tempos[nome].append(tempo)
    return tempos, resultados


def escolher_fontes_buscas(recorte_10, quantidade=3, semente=SEMENTE):
    """Usuarios de partida: sorteados entre os que tem seta de saida no recorte de 10%."""
    candidatos = sorted(u for u in recorte_10.nos() if recorte_10.grau_saida(u) > 0)
    if len(candidatos) < quantidade:
        raise ValueError(
            f"O recorte de 10% tem {len(candidatos)} usuarios com seta de saida; "
            f"sao necessarios pelo menos {quantidade} para o benchmark."
        )
    return random.Random(semente).sample(candidatos, quantidade)


def sortear_piloto(dados, por_tipo=5, semente=SEMENTE):
    """As mesmas dez marcacoes do piloto do notebook (cinco de amigo e cinco de inimigo)."""
    return pd.concat([
        dados.loc[dados["sinal"] == 1].sample(n=por_tipo, random_state=semente),
        dados.loc[dados["sinal"] == -1].sample(n=por_tipo, random_state=semente),
    ], ignore_index=True)


def escolher_fonte_bellman_ford(recorte_10, recorte_100):
    """Usuario sem ciclo negativo no recorte de 10% (com algum custo negativo) e com ciclo na rede completa.

    Entre os candidatos do recorte de 10%, prefere quem alcanca mais usuarios; no empate, o menor ID.
    """
    candidatos = []
    for usuario in sorted(recorte_10.nos()):
        distancias, _, ciclo = bellman_ford(recorte_10, usuario)
        if ciclo is None and min(distancias.values()) < 0:
            candidatos.append((usuario, len(distancias)))
    candidatos.sort(key=lambda candidato: (-candidato[1], candidato[0]))

    for usuario, _ in candidatos:
        if bellman_ford(recorte_100, usuario)[2] is not None:
            return usuario
    raise ValueError("Nenhum usuario atende aos dois casos do Bellman-Ford (sem ciclo e com ciclo).")


def executar_benchmark(dados, nome_dataset, repeticoes=REPETICOES, avisar=print):
    """Mede os quatro algoritmos como no notebook e devolve o conteudo do parte2_report.json."""
    avisar("Montando o grafo e os recortes de 10%, 50% e 100%...")
    grafo = montar_grafo_dataset(dados)
    recortes = montar_recortes(grafo)
    recortes_dijkstra = {percentual: grafo_com_pesos_dijkstra(g) for percentual, g in recortes.items()}
    fontes = escolher_fontes_buscas(recortes[10])
    avisar(f"Usuarios de partida: {', '.join(map(str, fontes))}")
    medicoes = []

    # BFS e DFS nos recortes
    for percentual, recorte in recortes.items():
        avisar(f"BFS e DFS no recorte de {percentual}%...")
        for fonte in fontes:
            tempos, resultados = medir_em_par([("BFS", bfs), ("DFS", dfs)], recorte, fonte, repeticoes)
            ordem_bfs = resultados["BFS"][2]
            ordem_dfs = resultados["DFS"][1]
            if set(ordem_bfs) != set(ordem_dfs):
                raise RuntimeError(f"BFS e DFS alcancaram usuarios diferentes a partir de {fonte}.")
            for nome in ("BFS", "DFS"):
                medicoes.append(medicao(
                    nome, "escalabilidade nos recortes", percentual, fonte, tempos[nome], SEM_PESOS,
                    alcancados=len(ordem_bfs),
                ))

    # Dijkstra e Bellman-Ford nos recortes, ambos com os pesos do Dijkstra
    for percentual, recorte in recortes_dijkstra.items():
        avisar(f"Dijkstra e Bellman-Ford no recorte de {percentual}%...")
        for fonte in fontes:
            tempos, resultados = medir_em_par(
                [("Dijkstra", dijkstra), ("Bellman-Ford", bellman_ford)], recorte, fonte, repeticoes
            )
            custos_dijkstra = resultados["Dijkstra"][0]
            custos_bf, _, ciclo = resultados["Bellman-Ford"]
            if ciclo is not None or custos_dijkstra != custos_bf:
                raise RuntimeError(f"Dijkstra e Bellman-Ford calcularam custos diferentes a partir de {fonte}.")
            for nome in ("Dijkstra", "Bellman-Ford"):
                medicoes.append(medicao(
                    nome, "escalabilidade nos recortes", percentual, fonte, tempos[nome], PESOS_DIJKSTRA,
                    alcancados=len(custos_dijkstra),
                ))

    # Dijkstra na volta das dez marcacoes do piloto (rede completa)
    avisar("Dijkstra nas marcacoes do piloto...")
    grafo_dijkstra = recortes_dijkstra[100]
    for origem, destino, _ in sortear_piloto(dados).itertuples(index=False, name=None):
        tempos = []
        for _ in range(repeticoes):
            (custos, pai, _), tempo = cronometrar(dijkstra, grafo_dijkstra, destino)
            tempos.append(tempo)
        caminho = montar_caminho(pai, origem)
        medicoes.append(medicao(
            "Dijkstra", "volta das marcações do piloto", 100, destino, tempos, PESOS_DIJKSTRA,
            destino=int(origem),
            custo=int(custos[origem]) if caminho else None,
            passos=len(caminho) - 1 if caminho else None,
        ))

    # Bellman-Ford com os sinais originais: sem ciclo (recorte de 10%) e com ciclo (rede completa)
    avisar("Bellman-Ford com os sinais originais...")
    fonte_bf = escolher_fonte_bellman_ford(recortes[10], recortes[100])

    tempos = []
    for _ in range(repeticoes):
        (distancias_bf, _, ciclo), tempo = cronometrar(bellman_ford, recortes[10], fonte_bf)
        tempos.append(tempo)
    medicoes.append(medicao(
        "Bellman-Ford", "peso negativo sem ciclo negativo", 10, fonte_bf, tempos, SINAIS,
        alcancados=len(distancias_bf), ciclo_negativo=None,
    ))

    tempos = []
    for _ in range(repeticoes):
        (_, _, ciclo_negativo), tempo = cronometrar(bellman_ford, recortes[100], fonte_bf)
        tempos.append(tempo)
    medicoes.append(medicao(
        "Bellman-Ford", "detecção de ciclo negativo", 100, fonte_bf, tempos, SINAIS,
        ciclo_negativo=[int(usuario) for usuario in ciclo_negativo],
        custo_ciclo=int(custo_caminho(recortes[100], ciclo_negativo)),
    ))

    return {
        "dataset": nome_dataset,
        "nos": grafo.ordem(),
        "arcos": grafo.tamanho(),
        "recortes": [
            {
                "usuarios (%)": percentual,
                "nos": recorte.ordem(),
                "arcos": recorte.tamanho(),
                "arcos (%)": round(recorte.tamanho() / grafo.tamanho() * 100, 2),
            }
            for percentual, recorte in recortes.items()
        ],
        "unidade_tempo": "milissegundos",
        "medicoes": medicoes,
    }


def salvar_relatorio(relatorio, pasta_saida):
    caminho = Path(pasta_saida) / "parte2_report.json"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho
