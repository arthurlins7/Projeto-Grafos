from collections import deque

def bfs(grafo, origem):
    if not grafo.tem_no(origem):
        raise KeyError(f"No de origem {origem} nao existe no grafo {grafo.nome}")

    dist = {origem: 0}
    pai = {origem: None}
    ordem_visita = []

    fila = deque([origem])
    while fila:
        u = fila.popleft()
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