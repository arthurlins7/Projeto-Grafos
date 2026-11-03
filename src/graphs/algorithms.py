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