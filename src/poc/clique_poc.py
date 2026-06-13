import networkx
import random

prefix = [i for i in range(10)]
suffix = [i+100 for i in range(10)]

random.seed(1)

wanted:list[tuple[int, int]] = []
G = networkx.Graph()

for p in prefix:
    for s in suffix:
        if random.random() < 0.2:
            wanted.append((p, s))
            G.add_node((p, s))

edge_count = 0

for w1 in wanted:
    for w2 in wanted:
        if (w1[0] == w2[0] or w1[1] == w2[1]) and w1 != w2:
            G.add_edge(w1, w2)
            edge_count += 1


print(G.nodes)
print(f"{edge_count} edges added.")



max_set, found_cliques = networkx.approximation.clique_removal(G)

print(f"Maximum Independent Set: {max_set}")
print(f"Found Cliques: {found_cliques}")