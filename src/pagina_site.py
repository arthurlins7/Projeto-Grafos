# [IA] Claude - dados do site (web/data.js) e o site inteiro num arquivo so (out/parte1/labirinto_interativo.html)
"""Gera os dados do site do grupo e junta as paginas de web/ num unico HTML.

- gerar_data_js(): grava web/data.js, usado pelas paginas em web/.
- gerar_site_unico(): junta todas as paginas de web/ (CSS, JavaScript, dados e imagens dentro)
  em out/parte1/labirinto_interativo.html, que abre direto no navegador.

Os resultados da Parte 1 sao calculados aqui com as funcoes do src/solve.py, entao um mapa novo
(o mapa surpresa) entra no site com --mapa novo.txt --interactive.
"""
import base64
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from src.graphs.algorithms import bfs, dfs, dijkstra
from src.graphs.estados import NO_ALVO, construir_grafo_estados, decompor_estado, grafo_estados_sem_alvo
from src.graphs.io import ler_mapa
from src.solve import (
    PASTA_MAPAS_GRUPO,
    PASTA_SAIDA,
    camadas_do_mapa,
    chave_de_leitura,
    chave_na_pagina,
    estado_inicial,
    estados_armadilha,
    listar_mapas,
    metricas_do_mapa,
    percurso_com_custos,
    resolver_mapa,
    resumo_graus,
)


PASTA_WEB = Path("web")
PASTA_OUT = Path("out")
PAGINAS = [  # (id da pagina no site unico, arquivo em web/, nome no menu)
    ("inicio", "index.html", "Início"),
    ("labirintos", "labirintos.html", "Labirintos"),
    ("modelagem", "modelagem.html", "Modelagem"),
    ("slashdot", "slashdot.html", "Slashdot"),
    ("graficos", "graficos.html", "Gráficos"),
    ("equipe", "equipe.html", "Equipe"),
]
ALGORITMOS = ["BFS", "DFS", "DIJKSTRA", "BELLMAN_FORD"]
LIMITE_ESTADOS = 8000    # acima disso a pagina mostra so os resumos (o grafo ficaria pesado demais no navegador)
LIMITE_ARCOS = 20000


def sem_traco(chaves):
    # o site usa "" para "sem chaves" (o rotulo do estado usa "-")
    return "" if chaves == "-" else chaves


def ordem_de_visita(g_est, inicio, algoritmo, limite=4000):
    # mapa sem solucao: a pagina anima a busca visitando os estados ate esgotar
    if algoritmo == "DFS":
        pai, ordem, classificacao, tem_ciclo = dfs(g_est, inicio)
    elif algoritmo == "DIJKSTRA" and not g_est.tem_peso_neg:
        dist, pai, ordem = dijkstra(g_est, inicio)
    else:
        dist, pai, ordem = bfs(g_est, inicio)
    visitas = []
    for estado in ordem[:limite]:
        if estado != NO_ALVO:
            posicao, chaves, bonus = decompor_estado(estado)
            visitas.append([posicao[0], posicao[1], sem_traco(chaves), list(bonus)])
    return visitas


def solucao_para_o_site(r, grafo, inicio, alg):
    sol = {
        "passos": r.get("passos"),
        "custo": r.get("custo"),
        "status": r["status"],
        "mensagem": r.get("mensagem"),
        "custo_ciclo": r.get("custo_ciclo"),
        "ciclo_fora_da_rota": r.get("custo_ciclo_fora_da_rota"),
        "caminho": [],
        "estados": [],   # [linha, coluna, chaves, bonus consumidos, custo acumulado] em cada passo
        "visitas": [],   # so quando nao tem solucao
    }
    estados = r.get("caminho") or r.get("ciclo") or []
    for l, c, chaves, bonus, custo in percurso_com_custos(grafo, estados):
        sol["caminho"].append([l, c])
        sol["estados"].append([l, c, sem_traco(chaves), bonus, custo])
    if r["status"] == "SEM_SOLUCAO":
        sol["visitas"] = ordem_de_visita(grafo, inicio, alg)
    return sol


def dados_de_um_mapa(caminho, nome, titulo):
    linhas = ler_mapa(caminho)
    g_est = construir_grafo_estados(linhas)
    sem_alvo = grafo_estados_sem_alvo(g_est)
    inicio = estado_inicial(linhas)

    solucoes = {}
    for alg in ALGORITMOS:
        r = resolver_mapa(linhas, alg)
        solucoes[alg] = solucao_para_o_site(r, g_est, inicio, alg)
        if alg == "DFS":
            dfs_info = {"arcos_por_tipo": r["arcos_por_tipo"], "tem_ciclo": r["tem_ciclo"]}
    if solucoes["BELLMAN_FORD"]["status"] == "CICLO_NEGATIVO":
        # a correcao do m06 so entra quando a regra original da ciclo negativo
        # (com muitas fontes ela multiplica os estados, entao nao roda a toa)
        r = resolver_mapa(linhas, "BELLMAN_FORD", fonte_consumivel=True)
        corrigido = construir_grafo_estados(linhas, fonte_consumivel=True)
        solucoes["BELLMAN_FORD_FONTE_CONSUMIVEL"] = solucao_para_o_site(r, corrigido, inicio, "BELLMAN_FORD")

    # camadas tiradas dos estados (nao dos arcos): um estado isolado tambem conta
    casas = defaultdict(set)
    for no in sem_alvo.nos():
        posicao, chaves, bonus = decompor_estado(no)
        casas[sem_traco(chaves)].add(posicao)
    info = camadas_do_mapa(sem_alvo)
    camadas = {
        "ordem": sorted(casas, key=lambda k: (len(k), k)),
        "casas": {k: sorted([l, c] for l, c in v) for k, v in casas.items()},
        "arcos_entre_camadas": info["arcos_entre_camadas"],
        "info": {sem_traco(k): v for k, v in info["camadas"].items()},
    }

    armadilhas = []
    for estado in estados_armadilha(g_est):
        posicao, chaves, bonus = decompor_estado(estado)
        armadilhas.append([posicao[0], posicao[1], sem_traco(chaves)])

    resumo = resumo_graus(linhas, g_est)
    numeros = {
        "estados": sem_alvo.ordem(),
        "maior_grau_saida": resumo["maior_grau_saida"],
        "maior_grau_entrada": resumo["maior_grau_entrada"],
        "multiplicidade_maxima": resumo["multiplicidade_maxima"],
        "becos": len(resumo["becos"]),
        "armadilhas": resumo["quantidade_armadilhas"],
        "dfs": dfs_info,
    }
    mapa = {"id": nome, "nome": titulo, "grade": linhas}
    return mapa, solucoes, metricas_do_mapa(linhas), armadilhas, camadas, numeros, grafo_para_o_site(g_est, sem_alvo, inicio)


def grafo_para_o_site(g_est, sem_alvo, inicio):
    # estados e arcos do G_est (sem o ALVO) para as visualizacoes interativas:
    # arvore da BFS, grafo em camadas, heatmap e as tabelas de arcos e graus.
    # cada estado: [linha, coluna, chaves, bonus, grau de entrada, grau de saida, nivel na BFS, indice do pai]
    # cada arco: [indice da origem, indice do destino, movimento, casa de destino, peso]
    if sem_alvo.ordem() > LIMITE_ESTADOS or sem_alvo.tamanho() > LIMITE_ARCOS:
        return {"cortado": True, "estados": [], "arcos": []}
    dist, pai, ordem = bfs(g_est, inicio)
    nos = [no for no in ordem if no != NO_ALVO]
    nos += sorted((no for no in sem_alvo.nos() if no not in dist), key=chave_de_leitura)
    indice = {no: i for i, no in enumerate(nos)}
    estados = []
    for no in nos:
        posicao, chaves, bonus = decompor_estado(no)
        estados.append([posicao[0], posicao[1], sem_traco(chaves), list(bonus),
                        sem_alvo.grau_entrada(no), sem_alvo.grau_saida(no),
                        dist.get(no, -1), indice.get(pai.get(no), -1)])
    arcos = []
    for no in nos:
        for destino, peso, movimento, casa in sem_alvo.vizinhos(no):
            arcos.append([indice[no], indice[destino], movimento, casa, peso])
    return {"cortado": False, "estados": estados, "arcos": arcos}


def arquivos_de_out(pasta=PASTA_SAIDA):
    # todos os CSV e JSON de out/parte1, para a pagina mostrar e deixar baixar
    arquivos = []
    for arquivo in sorted(Path(pasta).glob("*")):
        if arquivo.suffix in (".csv", ".json"):
            arquivos.append({"nome": arquivo.name, "tipo": arquivo.suffix[1:],
                             "texto": arquivo.read_text(encoding="utf-8")})
    return arquivos


def titulo_do_mapa(caminho):
    partes = Path(caminho).stem.split("_", 1)
    if len(partes) > 1:
        return partes[1].replace("_", " ").capitalize()
    if Path(caminho).parent.resolve() == PASTA_MAPAS_GRUPO.resolve():
        return "Mapa do grupo"
    return "Mapa novo"


def ler_json(caminho):
    caminho = Path(caminho)
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else None


def ler_parte2():
    # resumo do parte2_report.json para a pagina Slashdot (mesma logica do build_data.py antigo)
    rel = ler_json(PASTA_OUT / "parte2" / "parte2_report.json")
    if rel is None:
        return None
    tempos = defaultdict(list)
    piloto = []
    extras = {}
    for m in rel["medicoes"]:
        if m["tarefa"] == "escalabilidade nos recortes":
            alg = "Dijkstra" if m["algoritmo"].lower() == "dijkstra" else m["algoritmo"]
            tempos[(alg, m["recorte_percentual"])].append(m["tempo_mediano_ms"])
        elif m["tarefa"].startswith("volta"):
            piloto.append({
                "origem": m["usuario_partida"], "destino": m["destino"],
                "custo": m["custo"], "passos": m["passos"],
            })
        else:
            extras[m["tarefa"]] = m
    escala = []
    for (alg, rec), v in tempos.items():
        escala.append({"alg": alg, "recorte": rec, "ms": round(sum(v) / len(v), 2)})
    return {
        "dataset": rel["dataset"], "nos": rel["nos"], "arcos": rel["arcos"],
        "recortes": rel["recortes"], "escala": escala, "piloto": piloto,
        "ciclo": extras.get("detecção de ciclo negativo", {}).get("ciclo_negativo"),
        "custo_ciclo": extras.get("detecção de ciclo negativo", {}).get("custo_ciclo"),
    }


def dados_do_site(mapa_extra=None):
    # devolve (dados, nome do mapa extra no site)
    caminhos = listar_mapas()
    chave_extra = None
    if mapa_extra is not None:
        mapa_extra = Path(mapa_extra)
        if not any(c.resolve() == mapa_extra.resolve() for c in caminhos):
            caminhos.append(mapa_extra)

    dados = {"mapas": {}, "solucoes": {}, "metricas": {}, "armadilhas": {}, "camadas": {}, "numeros": {}, "grafos": {}}
    for caminho in caminhos:
        nome = chave_na_pagina(caminho, dados["mapas"])
        if mapa_extra is not None and Path(caminho).resolve() == mapa_extra.resolve():
            chave_extra = nome
        mapa, solucoes, metricas, armadilhas, camadas, numeros, grafo = dados_de_um_mapa(caminho, nome, titulo_do_mapa(caminho))
        dados["mapas"][nome] = mapa
        dados["solucoes"][nome] = solucoes
        dados["metricas"][nome] = metricas
        dados["armadilhas"][nome] = armadilhas
        dados["camadas"][nome] = camadas
        dados["numeros"][nome] = numeros
        dados["grafos"][nome] = grafo

    # resultados que o solve.py ja gravou em out/parte1
    dados["modelagem"] = []
    if (PASTA_SAIDA / "comparacao_modelagem.csv").exists():
        with open(PASTA_SAIDA / "comparacao_modelagem.csv", encoding="utf-8") as arquivo:
            dados["modelagem"] = list(csv.DictReader(arquivo))
    dados["ciclo_m06"] = ler_json(PASTA_SAIDA / "ciclo_negativo_m06.json")
    dados["gabarito"] = ler_json(PASTA_SAIDA / "gabarito_mapas_grupo.json")
    dados["parte2"] = ler_parte2()
    dados["arquivos"] = arquivos_de_out()
    return dados, chave_extra


def gerar_data_js(destino=PASTA_WEB / "data.js", mapa_extra=None):
    dados, chave = dados_do_site(mapa_extra)
    destino = Path(destino)
    destino.write_text("// [IA] Claude – arquivo gerado por src/pagina_site.py (python web/build_data.py)\n"
                       "window.DADOS = " + json.dumps(dados, ensure_ascii=False) + ";\n", encoding="utf-8")
    return destino


# ---------------------------------------------------------------- site num arquivo so

def imagens_do_site():
    # as figuras de out/ viram data URI, para o HTML nao depender de outros arquivos
    imagens = {}
    for pasta in ("parte1", "parte2"):
        for png in sorted((PASTA_OUT / pasta).glob("*.png")):
            imagens[f"{pasta}/{png.name}"] = "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode("ascii")
    return imagens


def miolo(html, arquivo):
    # pega o que esta dentro do <main> de uma pagina de web/
    achou = re.search(r"<main[^>]*>(.*)</main>", html, re.S)
    if not achou:
        raise ValueError(f"web/{arquivo} precisa ter um <main>")
    return achou.group(1)


def trocar_links(html):
    # labirintos.html -> #labirintos (no site unico cada pagina vira uma secao)
    for pid, arquivo, nome in PAGINAS:
        html = re.sub(rf'href="{re.escape(arquivo)}(#[\w-]+)?"', lambda m: f'href="{m.group(1) or "#" + pid}"', html)
    return html


def gerar_site_unico(destino=PASTA_SAIDA / "labirinto_interativo.html", mapa_extra=None):
    paginas = {arquivo: (PASTA_WEB / arquivo).read_text(encoding="utf-8") for pid, arquivo, nome in PAGINAS}
    estilo = (PASTA_WEB / "style.css").read_text(encoding="utf-8")
    script = (PASTA_WEB / "app.js").read_text(encoding="utf-8")
    roteador = (PASTA_WEB / "site_unico.js").read_text(encoding="utf-8")
    dados, chave_extra = dados_do_site(mapa_extra)

    cabeca = re.search(r"<head>(.*)</head>", paginas["index.html"], re.S).group(1)
    cabeca = re.sub(r'<link rel="stylesheet" href="style.css">', "", cabeca)
    rodape = re.search(r"<footer>.*?</footer>", paginas["index.html"], re.S).group(0)

    menu = "".join(f'<a href="#{pid}" data-pagina="{pid}">{nome}</a>' for pid, arquivo, nome in PAGINAS)
    secoes = "".join(
        f'\n<div class="pagina" id="pg-{pid}" data-pagina="{pid}" hidden>{trocar_links(miolo(paginas[arquivo], arquivo))}</div>'
        for pid, arquivo, nome in PAGINAS
    )
    # "</script" dentro do JSON fecharia a tag antes da hora
    js_dados = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    js_imagens = json.dumps(imagens_do_site())

    html = f"""<!DOCTYPE html>
<!-- [IA] Claude – site do grupo num arquivo so, gerado por src/pagina_site.py a partir de web/ (nao edite aqui, edite em web/) -->
<html lang="pt-BR">
<head>{cabeca}<style>
{estilo}
</style>
</head>
<body class="site-unico">
<div class="bg-orbs" aria-hidden="true"><span></span><span></span><span></span></div>
<header class="nav">
  <a class="brand" href="#inicio"><span class="brand-dot"></span>Projeto Grafos</a>
  <nav>{menu}</nav>
</header>
<main id="topo">{secoes}
</main>
{rodape}
<div class="lightbox" id="lightbox" hidden><img alt=""><p></p></div>
<script>
window.DADOS = {js_dados};
window.IMAGENS = {js_imagens};
window.MAPA_INICIAL = {json.dumps(chave_extra or "")};
</script>
<script>
{script}
</script>
<script>
{roteador}
</script>
</body>
</html>
"""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino
