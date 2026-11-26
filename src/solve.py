# [IA] Claude - implementacao escrita com apoio de IA, revisada e testada pelo grupo

import json
from pathlib import Path

import csv

from src.graphs.algorithms import bellman_ford, bfs, custo_caminho, dfs, dijkstra, montar_caminho
from src.graphs.io import ler_mapa, localizar_inicio_e_saidas, salvar_arestas_csv, salvar_graus_csv
from src.graphs.estados import (
    NO_ALVO,
    calcular_teto_teorico,
    construir_grafo_estados,
    construir_grafo_posicoes,
    decompor_estado,
    formatar_estado,
    grafo_estados_sem_alvo,
)


PASTA_MAPAS = Path("data/mapas")
PASTA_MAPAS_GRUPO = Path("data/mapas_grupo")
PASTA_SAIDA = Path("out/parte1")
PAGINA_INTERATIVA = PASTA_SAIDA / "labirinto_interativo.html"
MODELO_PAGINA = Path(__file__).parent / "labirinto_template.html"


def listar_mapas(pasta=None):
    # sem pasta: mapas fornecidos (m01 a m08) e depois os mapas do grupo
    if pasta is None:
        return sorted(PASTA_MAPAS.glob("*.txt")) + sorted(PASTA_MAPAS_GRUPO.glob("*.txt"))
    return sorted(Path(pasta).glob("*.txt"))


def nome_curto(caminho):
    # "data/mapas/m03_tres_chaves.txt" -> "m03"
    return Path(caminho).stem.split("_")[0]


def salvar_json(dados, caminho):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


def metricas_do_mapa(linhas):
    g_pos = construir_grafo_posicoes(linhas)
    g_est = grafo_estados_sem_alvo(construir_grafo_estados(linhas))
    teto = calcular_teto_teorico(linhas)
    return {
        "G_pos": g_pos.metricas(),
        "G_est": g_est.metricas(),
        "teto_teorico": teto,
        "taxa_ocupacao": g_est.ordem() / teto,
    }


def camadas_do_mapa(g_est):
    # g_est aqui ja vem sem o ALVO
    camada_de = {}
    nos_por_camada = {}
    for no in g_est.nos():
        posicao, chaves, bonus = decompor_estado(no)
        camada_de[no] = chaves
        if chaves not in nos_por_camada:
            nos_por_camada[chaves] = []
        nos_por_camada[chaves].append(no)

    camadas = {}
    for chaves, lista in nos_por_camada.items():
        camadas[chaves] = g_est.subgrafo_induzido(lista).metricas()

    arcos_entre = 0
    casas = {}
    for origem in g_est.nos():
        for destino, peso, mov, casa in g_est.vizinhos(origem):
            if camada_de[origem] != camada_de[destino]:
                arcos_entre += 1
                posicao, chaves, bonus = decompor_estado(destino)
                chave_casa = f"({posicao[0]},{posicao[1]}) {casa}"
                casas[chave_casa] = casas.get(chave_casa, 0) + 1

    return {
        "camadas": camadas,
        "arcos_entre_camadas": arcos_entre,
        "casas_que_mudam_de_camada": casas,
    }


def gerar_arestas_metricas_camadas(pasta_mapas=None, pasta_saida=PASTA_SAIDA):
    pasta_saida = Path(pasta_saida)
    metricas = {}
    camadas = {}

    for caminho in listar_mapas(pasta_mapas):
        nome = nome_curto(caminho)
        linhas = ler_mapa(caminho)
        g_est = construir_grafo_estados(linhas)

        salvar_arestas_csv(g_est, pasta_saida / f"arestas_{nome}.csv")
        salvar_graus_csv(g_est, pasta_saida / f"graus_{nome}.csv")

        metricas[nome] = metricas_do_mapa(linhas)
        camadas[nome] = camadas_do_mapa(grafo_estados_sem_alvo(g_est))

    salvar_json(metricas, pasta_saida / "metricas_global.json")
    salvar_json(camadas, pasta_saida / "camadas.json")
    return metricas, camadas


# ----------------------------------------------------------------------------
# Bloco 2: graus, comparacao de modelagens, algoritmos, percurso, ciclo e armadilhas
# ----------------------------------------------------------------------------

def salvar_csv(linhas_csv, colunas, caminho):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(colunas)
        for linha in linhas_csv:
            escritor.writerow(linha)


def estado_inicial(linhas):
    inicio, saidas = localizar_inicio_e_saidas(linhas)
    return formatar_estado(inicio[0], inicio[1])


def chave_de_leitura(rotulo):
    # ordem de leitura do rotulo: linha, coluna, chaves, bonus
    posicao, chaves, bonus = decompor_estado(rotulo)
    return (posicao[0], posicao[1], chaves, bonus)


def estados_que_chegam_no_alvo(g_est):
    # quem chega no ALVO = quem a BFS alcanca saindo do ALVO no grafo transposto
    if not g_est.tem_no(NO_ALVO):
        return set()
    dist, pai, ordem = bfs(g_est.transposto(), NO_ALVO)
    return set(dist)


def estados_armadilha(g_est):
    chegam = estados_que_chegam_no_alvo(g_est)
    armadilhas = []
    for no in g_est.nos():
        if no != NO_ALVO and no not in chegam:
            armadilhas.append(no)
    return armadilhas


def bellman_ford_ate_alvo(g_est, inicio):
    # Bellman-Ford pensando no caminho ate o ALVO.
    # Um ciclo negativo so atrapalha se dele ainda da pra chegar no ALVO.
    # Se o ciclo fica num lugar de onde nao se chega mais na saida, o menor custo
    # ate o ALVO continua definido: roda de novo so com os estados que chegam no ALVO.
    # devolve (dist, pai, ciclo que atrapalha ou None, ciclo fora da rota ou None)
    dist, pai, ciclo = bellman_ford(g_est, inicio)
    if ciclo is None:
        return dist, pai, None, None

    chegam = estados_que_chegam_no_alvo(g_est)
    if any(estado in chegam for estado in ciclo):
        return dist, pai, ciclo, None

    if inicio not in chegam:
        # nem o inicio chega no ALVO: nao tem caminho, com ou sem ciclo
        return {inicio: 0}, {inicio: None}, None, ciclo

    sub = g_est.subgrafo_induzido(chegam)
    dist, pai, ciclo_na_rota = bellman_ford(sub, inicio)
    return dist, pai, ciclo_na_rota, ciclo


def resumo_graus(linhas, g_est):
    sem_alvo = grafo_estados_sem_alvo(g_est)
    nos = sorted(sem_alvo.nos(), key=chave_de_leitura)

    maior_saida = nos[0]
    maior_entrada = nos[0]
    for no in nos:
        if sem_alvo.grau_saida(no) > sem_alvo.grau_saida(maior_saida):
            maior_saida = no
        if sem_alvo.grau_entrada(no) > sem_alvo.grau_entrada(maior_entrada):
            maior_entrada = no

    multiplicidade = {}
    for no in nos:
        posicao, chaves, bonus = decompor_estado(no)
        multiplicidade[posicao] = multiplicidade.get(posicao, 0) + 1
    maximo = max(multiplicidade.values())
    casas_maximo = [f"({l},{c})" for (l, c), m in sorted(multiplicidade.items()) if m == maximo]

    becos = []
    for no in nos:
        posicao, chaves, bonus = decompor_estado(no)
        if sem_alvo.grau_saida(no) == 0 and linhas[posicao[0]][posicao[1]] != "G":
            becos.append(no)

    return {
        "maior_grau_saida": {"estado": maior_saida, "grau": sem_alvo.grau_saida(maior_saida)},
        "maior_grau_entrada": {"estado": maior_entrada, "grau": sem_alvo.grau_entrada(maior_entrada)},
        "multiplicidade_maxima": maximo,
        "casas_com_multiplicidade_maxima": casas_maximo,
        "becos": becos,
        "quantidade_armadilhas": len(estados_armadilha(g_est)),
    }


def multiplicidade_das_casas(g_est):
    multiplicidade = {}
    for no in grafo_estados_sem_alvo(g_est).nos():
        posicao, chaves, bonus = decompor_estado(no)
        multiplicidade[posicao] = multiplicidade.get(posicao, 0) + 1
    return multiplicidade


def caminho_respeita_portas(linhas, caminho):
    # anda pelo caminho de casas e confere se cada porta foi aberta com a chave certa
    chaves = set()
    for linha, coluna in caminho:
        simbolo = linhas[linha][coluna]
        if simbolo in "abcd":
            chaves.add(simbolo)
        if simbolo in "ABCD" and simbolo.lower() not in chaves:
            return False
    return True


def bfs_ate_saida_g_pos(linhas, portas_como):
    g_pos = construir_grafo_posicoes(linhas, portas_como=portas_como)
    inicio, saidas = localizar_inicio_e_saidas(linhas)
    dist, pai, ordem = bfs(g_pos, inicio)
    melhor = None
    for saida in saidas:
        if saida in dist and (melhor is None or dist[saida] < dist[melhor]):
            melhor = saida
    if melhor is None:
        return None, None
    return dist[melhor], montar_caminho(pai, melhor)


def comparar_modelagens(pasta_mapas=None, pasta_saida=PASTA_SAIDA, mapas=("m02", "m03", "m04")):
    linhas_csv = []
    for caminho in listar_mapas(pasta_mapas):
        nome = nome_curto(caminho)
        if nome not in mapas:
            continue
        linhas = ler_mapa(caminho)

        passos, percurso = bfs_ate_saida_g_pos(linhas, "chao")
        if passos is None:
            linhas_csv.append([nome, "G_pos portas como chao", "", False, "nao encontra caminho"])
        elif caminho_respeita_portas(linhas, percurso):
            linhas_csv.append([nome, "G_pos portas como chao", passos, True, "caminho valido"])
        else:
            linhas_csv.append([nome, "G_pos portas como chao", passos, False,
                               "atravessa porta sem ter a chave"])

        passos, percurso = bfs_ate_saida_g_pos(linhas, "parede")
        if passos is None:
            linhas_csv.append([nome, "G_pos portas como parede", "", False,
                               "nao encontra caminho: nao sabe que pode pegar a chave e voltar"])
        else:
            linhas_csv.append([nome, "G_pos portas como parede", passos, True, "caminho sem passar por porta"])

        g_est = construir_grafo_estados(linhas)
        dist, pai, ordem = bfs(g_est, estado_inicial(linhas))
        if NO_ALVO in dist:
            linhas_csv.append([nome, "G_est", dist[NO_ALVO] - 1, True,
                               "pega as chaves antes de passar pelas portas"])
        else:
            linhas_csv.append([nome, "G_est", "", False, "sem solucao"])

    salvar_csv(linhas_csv, ["mapa", "abordagem", "passos", "caminho_valido", "observacao"],
               Path(pasta_saida) / "comparacao_modelagem.csv")
    return linhas_csv


def contar_tipos_dfs(classificacao):
    # nao conta os arcos que vao para o ALVO
    contagem = {"arvore": 0, "retorno": 0, "avanco": 0, "cruzamento": 0}
    for u, v, tipo in classificacao:
        if v != NO_ALVO:
            contagem[tipo] += 1
    return contagem


def linha_solucao(nome, algoritmo, grafo, dist, pai):
    if NO_ALVO not in dist:
        return [nome, algoritmo, "", "", "SEM_SOLUCAO", ""]
    caminho = montar_caminho(pai, NO_ALVO)[:-1]   # tira o ALVO do fim
    passos = len(caminho) - 1
    custo = custo_caminho(grafo, caminho)
    return [nome, algoritmo, passos, custo, "OK", " -> ".join(caminho)]


def rodar_algoritmos(pasta_mapas=None, pasta_saida=PASTA_SAIDA):
    solucoes = []
    classificacao_dfs = []

    for caminho in listar_mapas(pasta_mapas):
        nome = nome_curto(caminho)
        linhas = ler_mapa(caminho)
        g_est = construir_grafo_estados(linhas)
        inicio = estado_inicial(linhas)

        dist, pai, ordem = bfs(g_est, inicio)
        solucoes.append(linha_solucao(nome, "BFS", g_est, dist, pai))

        try:
            dist, pai, ordem = dijkstra(g_est, inicio)
            solucoes.append(linha_solucao(nome, "DIJKSTRA", g_est, dist, pai))
        except ValueError as erro:
            solucoes.append([nome, "DIJKSTRA", "", "", "RECUSA", str(erro)])

        dist, pai, ciclo, fora_da_rota = bellman_ford_ate_alvo(g_est, inicio)
        if ciclo is not None:
            solucoes.append([nome, "BELLMAN_FORD", "", custo_caminho(g_est, ciclo),
                             "CICLO_NEGATIVO", " -> ".join(ciclo)])
            g_corrigido = construir_grafo_estados(linhas, fonte_consumivel=True)
            dist, pai, ciclo, fora_da_rota = bellman_ford_ate_alvo(g_corrigido, inicio)
            if ciclo is None:
                solucoes.append(linha_solucao(nome, "BELLMAN_FORD_FONTE_CONSUMIVEL", g_corrigido, dist, pai))
            else:
                solucoes.append([nome, "BELLMAN_FORD_FONTE_CONSUMIVEL", "", custo_caminho(g_corrigido, ciclo),
                                 "CICLO_NEGATIVO", " -> ".join(ciclo)])
        else:
            solucoes.append(linha_solucao(nome, "BELLMAN_FORD", g_est, dist, pai))

        pai, ordem, classificacao, tem_ciclo = dfs(g_est, inicio)
        # a DFS nao calcula distancia; o pai ja diz quem foi alcancado
        solucoes.append(linha_solucao(nome, "DFS", g_est, pai, pai))

        contagem = contar_tipos_dfs(classificacao)
        classificacao_dfs.append([nome, contagem["arvore"], contagem["retorno"],
                                  contagem["avanco"], contagem["cruzamento"], tem_ciclo])

    salvar_csv(solucoes, ["mapa", "algoritmo", "passos", "custo", "status", "caminho"],
               Path(pasta_saida) / "solucoes.csv")
    salvar_csv(classificacao_dfs, ["mapa", "arvore", "retorno", "avanco", "cruzamento", "tem_ciclo"],
               Path(pasta_saida) / "dfs_classificacao.csv")
    return solucoes, classificacao_dfs


def percurso_menor_custo(linhas):
    g_est = construir_grafo_estados(linhas)
    inicio = estado_inicial(linhas)
    if g_est.tem_peso_neg:
        dist, pai, ciclo, fora_da_rota = bellman_ford_ate_alvo(g_est, inicio)
        algoritmo = "BELLMAN_FORD"
        if ciclo is not None:
            # ciclo negativo que chega no ALVO: o menor custo nao existe
            return None
    else:
        dist, pai, ordem = dijkstra(g_est, inicio)
        algoritmo = "DIJKSTRA"
    if NO_ALVO not in dist:
        return None

    caminho = montar_caminho(pai, NO_ALVO)[:-1]
    passos = []
    acumulado = 0
    for i, estado in enumerate(caminho):
        if i > 0:
            acumulado += custo_caminho(g_est, [caminho[i - 1], estado])
        posicao, chaves, bonus = decompor_estado(estado)
        passos.append({
            "passo": i,
            "estado": estado,
            "linha": posicao[0],
            "coluna": posicao[1],
            "casa": linhas[posicao[0]][posicao[1]],
            "chaves": chaves,
            "bonus_consumidos": list(bonus),
            "custo_acumulado": acumulado,
        })
    return {"algoritmo": algoritmo, "passos": len(caminho) - 1, "custo_total": acumulado, "percurso": passos}


def ciclo_negativo(linhas):
    g_est = construir_grafo_estados(linhas)
    inicio = estado_inicial(linhas)
    dist, pai, ciclo = bellman_ford(g_est, inicio)
    resultado = {"tem_ciclo_negativo": ciclo is not None}
    if ciclo is not None:
        arcos = []
        for i in range(len(ciclo) - 1):
            arcos.append({"origem": ciclo[i], "destino": ciclo[i + 1],
                          "peso": custo_caminho(g_est, [ciclo[i], ciclo[i + 1]])})
        resultado["ciclo"] = ciclo
        resultado["arcos"] = arcos
        resultado["custo_do_ciclo"] = custo_caminho(g_est, ciclo)

    # correcao de regra: fonte consumivel (--fonte-consumivel)
    corrigido = construir_grafo_estados(linhas, fonte_consumivel=True)
    dist, pai, ciclo2 = bellman_ford(corrigido, inicio)
    resultado["com_fonte_consumivel"] = {
        "tem_ciclo_negativo": ciclo2 is not None,
        "custo_ate_alvo": dist.get(NO_ALVO) if ciclo2 is None else None,
    }
    return resultado


def resolver_mapa(linhas, algoritmo, fonte_consumivel=False):
    # usado pelo cli.py: roda um algoritmo no G_est de um mapa so
    g_est = construir_grafo_estados(linhas, fonte_consumivel=fonte_consumivel)
    inicio = estado_inicial(linhas)
    resultado = {
        "algoritmo": algoritmo,
        "fonte_consumivel": fonte_consumivel,
        "estados": grafo_estados_sem_alvo(g_est).ordem(),
    }

    if algoritmo == "BFS":
        dist, pai, ordem = bfs(g_est, inicio)
    elif algoritmo == "DIJKSTRA":
        try:
            dist, pai, ordem = dijkstra(g_est, inicio)
        except ValueError as erro:
            resultado["status"] = "RECUSA"
            resultado["mensagem"] = str(erro)
            return resultado
    elif algoritmo == "BELLMAN_FORD":
        dist, pai, ciclo, fora_da_rota = bellman_ford_ate_alvo(g_est, inicio)
        if ciclo is not None:
            resultado["status"] = "CICLO_NEGATIVO"
            resultado["ciclo"] = ciclo
            resultado["custo_ciclo"] = custo_caminho(g_est, ciclo)
            return resultado
        if fora_da_rota is not None:
            # tem ciclo negativo, mas dele nao da pra chegar na saida
            resultado["ciclo_fora_da_rota"] = fora_da_rota
            resultado["custo_ciclo_fora_da_rota"] = custo_caminho(g_est, fora_da_rota)
    elif algoritmo == "DFS":
        pai, ordem, classificacao, tem_ciclo = dfs(g_est, inicio)
        dist = pai   # a DFS nao calcula distancia; o pai ja diz quem foi alcancado
        resultado["arcos_por_tipo"] = contar_tipos_dfs(classificacao)
        resultado["tem_ciclo"] = tem_ciclo
    else:
        raise ValueError(f"Algoritmo desconhecido: {algoritmo}")

    linha = linha_solucao("", algoritmo, g_est, dist, pai)
    resultado["status"] = linha[4]
    if linha[4] == "OK":
        resultado["passos"] = linha[2]
        resultado["custo"] = linha[3]
        resultado["caminho"] = montar_caminho(pai, NO_ALVO)[:-1]
    return resultado


def armadilhas_do_mapa(linhas, fonte_consumivel=False):
    # usado pelo cli.py: estados-armadilha em ordem de leitura e o total de estados
    g_est = construir_grafo_estados(linhas, fonte_consumivel=fonte_consumivel)
    armadilhas = sorted(estados_armadilha(g_est), key=chave_de_leitura)
    return armadilhas, grafo_estados_sem_alvo(g_est).ordem()


def gabarito_do_mapa(linhas):
    # Secao 10: numeros que vao para o PDF (estados, arcos, passos e custo)
    g_est = construir_grafo_estados(linhas)
    sem_alvo = grafo_estados_sem_alvo(g_est)
    dist, pai, ordem = bfs(g_est, estado_inicial(linhas))
    armadilhas = estados_armadilha(g_est)
    resultado = percurso_menor_custo(linhas)

    gabarito = {
        "estados": sem_alvo.ordem(),
        "arcos": sem_alvo.tamanho(),
        "passos_bfs": dist[NO_ALVO] - 1 if NO_ALVO in dist else None,
        "custo": None,
        "algoritmo_custo": None,
        "pega_bonus": False,
        "passa_por_esteira": False,
        "armadilhas": len(armadilhas),
        "porcentagem_armadilhas": round(100 * len(armadilhas) / sem_alvo.ordem(), 1),
    }
    if resultado is not None:
        gabarito["custo"] = resultado["custo_total"]
        gabarito["algoritmo_custo"] = resultado["algoritmo"]
        gabarito["pega_bonus"] = any(p["casa"] == "+" for p in resultado["percurso"])
        gabarito["passa_por_esteira"] = any(p["casa"] in "><^v" for p in resultado["percurso"])
    return gabarito


def gerar_resultados_algoritmos(pasta_mapas=None, pasta_saida=PASTA_SAIDA):
    pasta_saida = Path(pasta_saida)

    resumo = {}
    for caminho in listar_mapas(pasta_mapas):
        linhas = ler_mapa(caminho)
        resumo[nome_curto(caminho)] = resumo_graus(linhas, construir_grafo_estados(linhas))
    salvar_json(resumo, pasta_saida / "graus_resumo.json")

    comparar_modelagens(pasta_mapas, pasta_saida)
    rodar_algoritmos(pasta_mapas, pasta_saida)

    for caminho in listar_mapas(pasta_mapas):
        nome = nome_curto(caminho)
        linhas = ler_mapa(caminho)
        if nome in ("m03", "m08", "g01"):
            salvar_json(percurso_menor_custo(linhas), pasta_saida / f"percurso_{nome}.json")
        if nome == "m06":
            salvar_json(ciclo_negativo(linhas), pasta_saida / "ciclo_negativo_m06.json")
        if nome in ("m04", "m07", "g02"):
            linhas_csv = []
            for estado in estados_armadilha(construir_grafo_estados(linhas)):
                posicao, chaves, bonus = decompor_estado(estado)
                linhas_csv.append([estado, posicao[0], posicao[1], linhas[posicao[0]][posicao[1]], chaves])
            salvar_csv(linhas_csv, ["estado", "linha", "coluna", "casa", "chaves"],
                       pasta_saida / f"armadilhas_{nome}.csv")

    gabarito = {}
    for caminho in listar_mapas(PASTA_MAPAS_GRUPO):
        gabarito[nome_curto(caminho)] = gabarito_do_mapa(ler_mapa(caminho))
    salvar_json(gabarito, pasta_saida / "gabarito_mapas_grupo.json")


# ----------------------------------------------------------------------------
# Bloco 3: figuras da Secao 8
# ----------------------------------------------------------------------------

def gerar_figuras(pasta_mapas=None, pasta_saida=PASTA_SAIDA):
    from src.viz import (desenhar_arvore_bfs, desenhar_camadas, desenhar_heatmap,
                         desenhar_percurso, salvar_figura)
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    for caminho in listar_mapas(pasta_mapas):
        nome = nome_curto(caminho)
        linhas = ler_mapa(caminho)

        if nome in ("m03", "m08", "g01"):
            resultado = percurso_menor_custo(linhas)
            fig, ax = desenhar_percurso(linhas, resultado["percurso"],
                                        f"{nome}: caminho de menor custo (custo {resultado['custo_total']})")
            salvar_figura(fig, pasta_saida / f"percurso_{nome}.png")

        if nome == "m02":
            g_est = construir_grafo_estados(linhas)
            fig, ax = desenhar_camadas(grafo_estados_sem_alvo(g_est), "m02: grafo de estados em camadas")
            salvar_figura(fig, pasta_saida / "camadas_m02.png")
            fig, ax = desenhar_arvore_bfs(g_est, estado_inicial(linhas), "m02: árvore da BFS no grafo de estados")
            salvar_figura(fig, pasta_saida / "arvore_bfs_m02.png")

        if nome == "m08":
            g_est = construir_grafo_estados(linhas)
            fig, ax = desenhar_heatmap(linhas, multiplicidade_das_casas(g_est),
                                       "m08: multiplicidade das casas (estados por casa)")
            salvar_figura(fig, pasta_saida / "heatmap_multiplicidade_m08.png")


# ----------------------------------------------------------------------------
# Secao 9: pagina interativa
# ----------------------------------------------------------------------------

def percurso_com_custos(g_est, caminho):
    # cada passo vira [linha, coluna, chaves, bonus consumidos, custo acumulado]
    passos = []
    acumulado = 0
    for i, estado in enumerate(caminho):
        if i > 0:
            acumulado += custo_caminho(g_est, [caminho[i - 1], estado])
        posicao, chaves, bonus = decompor_estado(estado)
        passos.append([posicao[0], posicao[1], chaves, list(bonus), acumulado])
    return passos


def dados_da_pagina():
    # tudo que a pagina interativa precisa, mapa por mapa
    dados = {}
    for caminho in listar_mapas():
        nome = nome_curto(caminho)
        linhas = ler_mapa(caminho)
        g_est = construir_grafo_estados(linhas)

        # camadas: casas que existem para cada conjunto de chaves
        camadas = {}
        for no in grafo_estados_sem_alvo(g_est).nos():
            posicao, chaves, bonus = decompor_estado(no)
            camadas.setdefault(chaves, set()).add(posicao)
        camadas = {k: sorted(camadas[k]) for k in sorted(camadas, key=lambda k: (len(k.strip("-")), k))}

        armadilhas = []
        for estado in estados_armadilha(g_est):
            posicao, chaves, bonus = decompor_estado(estado)
            armadilhas.append([posicao[0], posicao[1], chaves])

        nomes_alg = ["BFS", "DFS", "DIJKSTRA", "BELLMAN_FORD"]
        if any("*" in linha for linha in linhas):
            nomes_alg.append("BELLMAN_FORD_FONTE_CONSUMIVEL")

        algoritmos = {}
        for alg in nomes_alg:
            fonte = alg == "BELLMAN_FORD_FONTE_CONSUMIVEL"
            r = resolver_mapa(linhas, "BELLMAN_FORD" if fonte else alg, fonte)
            grafo = construir_grafo_estados(linhas, fonte_consumivel=True) if fonte else g_est
            percurso = []
            if "caminho" in r:
                percurso = percurso_com_custos(grafo, r["caminho"])
            elif "ciclo" in r:
                percurso = percurso_com_custos(grafo, r["ciclo"])
            algoritmos[alg] = {
                "status": r["status"],
                "passos": r.get("passos"),
                "custo": r.get("custo"),
                "mensagem": r.get("mensagem"),
                "custo_ciclo": r.get("custo_ciclo"),
                "percurso": percurso,
            }

        partes = Path(caminho).stem.split("_", 1)
        dados[nome] = {
            "titulo": partes[1].replace("_", " ") if len(partes) > 1 else "mapa do grupo",
            "grade": linhas,
            "camadas": camadas,
            "armadilhas": armadilhas,
            "algoritmos": algoritmos,
        }
    return dados


def gerar_pagina_interativa(destino=PAGINA_INTERATIVA):
    # o modelo (src/labirinto_template.html) tem o HTML e o JavaScript;
    # aqui so colocamos os dados dentro dele e salvamos em out/parte1/
    modelo = MODELO_PAGINA.read_text(encoding="utf-8")
    marcador = "/*DADOS*/{}"
    if marcador not in modelo:
        raise ValueError(f"O modelo {MODELO_PAGINA} precisa ter a linha: const DADOS = {marcador};")
    html = modelo.replace(marcador, json.dumps(dados_da_pagina(), ensure_ascii=False))
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino


if __name__ == "__main__":
    gerar_arestas_metricas_camadas()
    gerar_resultados_algoritmos()
    gerar_figuras()
    gerar_pagina_interativa()
    print(f"Arquivos gerados em {PASTA_SAIDA}/")