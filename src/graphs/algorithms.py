import heapq

def bfs(grafo, origem):
    if not grafo.tem_no(origem):
        raise KeyError(f"No de origem {origem} nao existe no grafo {grafo.nome}")

    dist = {origem: 0}
    pai = {origem: None}
    ordem_visita = []

    fila = [origem]
    inicio = 0
    while inicio < len(fila):
        u = fila[inicio]
        inicio += 1
        ordem_visita.append(u)
        for v, peso, mov, casa in grafo.vizinhos(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                pai[v] = u
                fila.append(v)

    return dist, pai, ordem_visita

def montar_caminho(pai, alvo):
    if alvo not in pai:
        return None

    caminho = []
    atual = alvo
    while atual is not None:
        caminho.append(atual)
        atual = pai[atual]
    caminho.reverse()
    return caminho

def dijkstra(grafo, origem):
    if not grafo.tem_no(origem):
        raise KeyError(f"No de origem {origem} nao existe no grafo {grafo.nome}")

    if grafo.tem_peso_neg:
        for u in grafo.nos():
            for v, peso, mov, casa in grafo.vizinhos(u):
                if peso < 0:
                    raise ValueError(f"Dijkstra nao aceita peso negativo: arco {u} -> {v} tem peso {peso}")

    dist = {origem: 0}
    pai = {origem: None}
    ordem_visita = []
    visitados = set()

    contador = 0
    heap = [(0, contador, origem)]
    while heap:
        d, _, u = heapq.heappop(heap)
        if u in visitados:
            continue
        visitados.add(u)
        ordem_visita.append(u)

        for v, peso, mov, casa in grafo.vizinhos(u):
            nova = d + peso
            if v not in dist or nova < dist[v]:
                dist[v] = nova
                pai[v] = u
                contador += 1
                heapq.heappush(heap, (nova, contador, v))

    return dist, pai, ordem_visita

def procurar_ciclo_pais(pai):
    # se os ponteiros de pai formam um ciclo, esse ciclo e negativo
    estado = {}  # 1 = no caminho atual, 2 = ja verificado
    for inicio in pai:
        if inicio in estado:
            continue
        caminho = []
        u = inicio
        while u is not None and u not in estado:
            estado[u] = 1
            caminho.append(u)
            u = pai[u]
        if u is not None and estado[u] == 1:
            i = caminho.index(u)
            ciclo = list(reversed(caminho[i:]))
            ciclo.append(ciclo[0])
            return ciclo
        for x in caminho:
            estado[x] = 2
    return None


def custo_caminho(grafo, caminho):
    total = 0
    for i in range(len(caminho) - 1):
        u = caminho[i]
        v = caminho[i + 1]
        menor = None
        for destino, peso, mov, casa in grafo.vizinhos(u):
            if destino == v and (menor is None or peso < menor):
                menor = peso
        if menor is None:
            raise ValueError(f"Nao existe arco {u} -> {v}")
        total += menor
    return total


def bellman_ford(grafo, origem):
    if not grafo.tem_no(origem):
        raise KeyError(f"No de origem {origem} nao existe no grafo {grafo.nome}")

    dist = {origem: 0}
    pai = {origem: None}
    mudaram = [origem]

    for rodada in range(grafo.ordem() - 1):
        proxima = []
        na_proxima = set()
        for u in mudaram:
            for v, peso, mov, casa in grafo.vizinhos(u):
                nova = dist[u] + peso
                if v not in dist or nova < dist[v]:
                    dist[v] = nova
                    pai[v] = u
                    if v not in na_proxima:
                        na_proxima.add(v)
                        proxima.append(v)

        if not proxima:
            return dist, pai, None

        ciclo = procurar_ciclo_pais(pai)
        if ciclo is not None:
            return dist, pai, ciclo

        mudaram = proxima

    for u in mudaram:
        for v, peso, mov, casa in grafo.vizinhos(u):
            if dist[u] + peso < dist[v]:
                pai[v] = u
                return dist, pai, procurar_ciclo_pais(pai)

    return dist, pai, None

def dfs(grafo, origem=None):
    if origem is not None and not grafo.tem_no(origem):
        raise KeyError(f"No de origem {origem} nao existe no grafo {grafo.nome}")

    descoberta = {}
    termino = {}
    pai = {}
    ordem_visita = []
    classificacao = []
    tempo = 0

    if origem is None:
        inicios = grafo.nos()
    else:
        inicios = [origem]

    for inicio in inicios:
        if inicio in descoberta:
            continue
        pai[inicio] = None
        tempo += 1
        descoberta[inicio] = tempo
        ordem_visita.append(inicio)

        # cada item da pilha e (no, indice do proximo vizinho a olhar)
        pilha = [(inicio, 0)]
        while pilha:
            u, i = pilha[-1]
            vizinhos = grafo.vizinhos(u)

            if i < len(vizinhos):
                pilha[-1] = (u, i + 1)
                v = vizinhos[i][0]
                if v not in descoberta:
                    classificacao.append((u, v, "arvore"))
                    pai[v] = u
                    tempo += 1
                    descoberta[v] = tempo
                    ordem_visita.append(v)
                    pilha.append((v, 0))
                elif v not in termino:
                    classificacao.append((u, v, "retorno"))
                elif descoberta[u] < descoberta[v]:
                    classificacao.append((u, v, "avanco"))
                else:
                    classificacao.append((u, v, "cruzamento"))
            else:
                pilha.pop()
                tempo += 1
                termino[u] = tempo

    tem_ciclo = False
    for u, v, tipo in classificacao:
        if tipo == "retorno":
            tem_ciclo = True
            break

    return pai, ordem_visita, classificacao, tem_ciclo