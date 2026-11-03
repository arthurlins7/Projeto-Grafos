# Grafo dirigido e ponderado em lista de adjacencia.
# Usado tanto na Parte 1 (labirintos) quanto na Parte 2 (Slashdot).


class GrafoDirigido:
    def __init__(self, nome=""):
        self.nome = nome
        self.adj = {}             # no -> lista de (destino, peso, movimento, casa)
        self.grau_ent = {}        # no -> grau de entrada
        self.qtd_arcos = 0
        self.tem_peso_neg = False

    def adicionar_no(self, no):
        if no not in self.adj:
            self.adj[no] = []
            self.grau_ent[no] = 0

    def adicionar_arco(self, origem, destino, peso=1, movimento="", casa=""):
        # so cria origem -> destino (grafo dirigido)
        # na Parte 2 movimento e casa ficam vazios
        self.adicionar_no(origem)
        self.adicionar_no(destino)
        self.adj[origem].append((destino, peso, movimento, casa))
        self.grau_ent[destino] += 1
        self.qtd_arcos += 1
        if peso < 0:
            self.tem_peso_neg = True

    def vizinhos(self, no):
        if no not in self.adj:
            raise KeyError(f"No {no} nao existe no grafo {self.nome}")
        return self.adj[no]

    def tem_no(self, no):
        return no in self.adj

    def nos(self):
        return list(self.adj.keys())

    def ordem(self):
        return len(self.adj)

    def tamanho(self):
        return self.qtd_arcos

    def densidade(self):
        n = self.ordem()
        if n < 2:
            return 0.0
        return self.qtd_arcos / (n * (n - 1))

    def grau_saida(self, no):
        return len(self.vizinhos(no))

    def grau_entrada(self, no):
        if no not in self.grau_ent:
            raise KeyError(f"No {no} nao existe no grafo {self.nome}")
        return self.grau_ent[no]

    def metricas(self):
        return {
            "ordem": self.ordem(),
            "tamanho": self.tamanho(),
            "densidade": self.densidade()
        }

    def tabela_graus(self):
        # (no, grau_entrada, grau_saida)
        tabela = []
        for no in self.adj:
            tabela.append((no, self.grau_ent[no], len(self.adj[no])))
        return tabela

    def subgrafo_induzido(self, lista_nos):
        manter = set(lista_nos)
        sub = GrafoDirigido(nome=self.nome + "_sub")
        for no in self.adj:  # percorre self.adj pra manter a ordem original
            if no in manter:
                sub.adicionar_no(no)
        for origem in self.adj:
            if origem not in manter:
                continue
            for destino, peso, mov, casa in self.adj[origem]:
                if destino in manter:
                    sub.adicionar_arco(origem, destino, peso, mov, casa)
        return sub

    def transposto(self):
        inv = GrafoDirigido(nome=self.nome + "_inv")
        for no in self.adj:
            inv.adicionar_no(no)
        for origem in self.adj:
            for destino, peso, mov, casa in self.adj[origem]:
                inv.adicionar_arco(destino, origem, peso, mov, casa)
        return inv