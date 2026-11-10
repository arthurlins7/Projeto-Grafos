# Regras Definidas do Projeto e dos Mapas (Teoria dos Grafos + AVD 2026.2)

Este arquivo consolida as regras do projeto e da modelagem dos mapas do labirinto.

---

## 1. Formato e Validação do Mapa (`src/graphs/io.py`)

- **Grade retangular**: todas as linhas devem ter o mesmo número de colunas.
- **Comentários**: linhas iniciadas com `;` na primeira coluna são ignoradas na leitura.
- **Coordenadas**: `(linha, coluna)` indexadas a partir de `0` (linha `0` no topo, coluna `0` à esquerda).
- **Validações obrigatórias com mensagem clara**:
  - Mapa vazio (`"O mapa nao pode estar vazio."`).
  - Linha vazia (`"A linha X do mapa esta vazia."`).
  - Grade não retangular (`"A linha X tem Y colunas; esperado: Z."`).
  - Símbolo desconhecido (`"Simbolo desconhecido 'X' na linha Y, coluna Z."`).
  - Quantidade de `S` diferente de 1 (`"O mapa deve ter exatamente um S; encontrados: X."`).
  - Nenhum `G` (`"O mapa deve ter pelo menos um G."`).

---

## 2. Símbolos, Comportamento e Custos de Entrada (`src/graphs/estados.py`)

> **Regra de peso:** O custo de um arco `u -> v` é sempre o **custo da casa de destino `v`**.

| Símbolo | Significado | Custo de entrar | Comportamento |
| :---: | :--- | :---: | :--- |
| `#` | Parede | — | Intransponível. Nunca gera nó nem arco de entrada. |
| `.` | Chão | `1` | Movimento livre. |
| `S` | Início | `1` | Ponto de partida (exatamente 1 por mapa). Ao retornar a `S`, comporta-se como chão (custo `1`). |
| `G` | Saída | `1` | Pelo menos 1 por mapa. Ao entrar em `G`, **o jogo termina**: estados posicionados em `G` **não têm arestas de saída** para casas vizinhas. |
| `,` | Lama | `3` | Terreno mais custoso. |
| `~` | Água | `5` | Terreno ainda mais custoso. |
| `a` `b` `c` `d` | Chave | `1` | Ao entrar, o jogador coleta a chave e **fica com ela para sempre** (união ao conjunto de chaves do estado). |
| `A` `B` `C` `D` | Porta | `1` | Só pode entrar quem já possui a chave minúscula correspondente (`a`->`A`, `b`->`B`, `c`->`C`, `d`->`D`). A porta não fecha e a chave não é gasta. Sem a chave, funciona como parede. |
| `>` `<` `^` `v` | Esteira | `1` | Pode-se entrar por qualquer direção; **estando nela**, o único movimento permitido de saída é na direção da seta (`^`=N, `>`=L, `v`=S, `<`=O). |
| `+` | Bônus consumível | `-4` (1ª vez)<br>`1` (depois) | Numerados de `0` em diante em ordem de leitura (linha, depois coluna). Na 1ª visita pelo caminho (quando o índice ainda não está no conjunto de bônus do estado), custa `-4` e é adicionado ao conjunto de bônus consumidos. Nas visitas seguintes no mesmo estado/caminho, comporta-se como chão (custo `1`). |
| `*` | Fonte de energia | `-2` (padrão) | Vale `-2` toda vez que o jogador entra (não se esgota, gerando ciclo negativo no `m06`). Com a opção `--fonte-consumivel`, passa a ser consumível como o bônus (vale `-2` na 1ª vez e `1` depois). |

---

## 3. Regras de Movimento (Ordem Obrigatória)

1. **Ordem de vizinhança**: sempre testada na ordem **N, L, S, O** (Cima, Direita, Baixo, Esquerda):
   - `N`: `(lin - 1, col)`
   - `L`: `(lin, col + 1)`
   - `S`: `(lin + 1, col)`
   - `O`: `(lin, col - 1)`
2. **Esteiras**: se a casa atual é `^`, `>`, `v` ou `<`, apenas o movimento correspondente (`N`, `L`, `S` ou `O`) é testado. Se apontar para parede ou porta trancada, o estado fica com grau de saída `0` (beco).
3. **Parada em `G`**: estados cuja posição é `G` não geram movimentos para vizinhos da grade (apenas o arco de custo `0` para o nó virtual `ALVO`).

---

## 4. Modelagem dos Grafos (`G_pos` e `G_est`)

- **`G_pos` (`construir_grafo_posicoes`)**:
  - Cada casa livre `(linha, coluna)` é um nó.
  - Suporta `portas_como="chao"` e `portas_como="parede"` (para comparar com `G_est` na Seção 6) e `bonus_fixo=True` (`+` valendo `-4` fixo para mostrar o ciclo negativo no `m05`).
- **`G_est` (`construir_grafo_estados`)**:
  - Rótulo obrigatório: `(linha,coluna)|chaves|{bonus}` (ex.: `(1,1)|-|{}`, `(3,5)|ab|{0,2}`).
  - Construído por BFS a partir do estado inicial (apenas estados alcançáveis).
  - Nó virtual `ALVO` recebe arco de peso `0` de todo estado posicionado em `G`.
  - Para métricas da Seção 3, `grafo_estados_sem_alvo(grafo)` remove `ALVO`.
- **Teto Teórico (`calcular_teto_teorico`)**:
  - `casas_livres * (2 ** num_chaves) * (2 ** num_bonus)`
