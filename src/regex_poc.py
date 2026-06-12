import json
import networkx
import re
import os
import random
from itertools import combinations

FILE_PATH, _ = os.path.split(os.path.realpath(__file__))

with open(f'{FILE_PATH}/../data/flask_mods.json', "r", encoding='utf-8') as f:
    affix = json.load(f)

prefix = {a["Name"] : a for a in affix if a["Prefix"] == True}
suffix = {a["Name"] : a for a in affix if a["Prefix"] == False}

p_names = [p for p in prefix]
s_names = [s for s in suffix]

def findPrefixNicnames(aff:list[dict], names:list[str]):
    for a in aff:
        for i in range(1, len(a["Name"])):
            nn = a["Name"][:i]
            for n in names:
                if n.startswith(nn) and a["Name"] != n:
                    break
            else:
                # print(f"{a["Name"]}\t => {nn}")
                a["Nicname"] = nn
                break
        else:
            print(f"ERROR: Nicname not found for {a["Name"]}.")

def findSuffixNicnames(aff:list[dict], names:list[str]):
    for a in aff:
        for i in range(1, len(a["Name"]) + 1):
            nn = a["Name"][-i:]
            for n in names:
                if n.endswith(nn) and a["Name"] != n:
                    break
            else:
                # print(f"{a["Name"]}\t => {nn}")
                a["Nicname"] = nn
                break
        else:
            print(f"ERROR: Nicname not found for {a["Name"]}.")


findPrefixNicnames(prefix.values(), p_names)
findSuffixNicnames(suffix.values(), s_names)

random.seed(1)

base = "Jade Flask"

G = networkx.Graph()
flasks = []
wanted:list[tuple[str, str]] = []

for p in prefix:
    for s in suffix:
        full_name = f"{p} {base} {s}"
        flasks.append(full_name)
        if random.random() < 0.2:
            wanted.append((p, s))
            G.add_node((p, s))

print(f"{len(flasks)} unique flask conbinations")



edge_count = 0

for w1 in wanted:
    for w2 in wanted:
        if (w1[0] == w2[0] or w1[1] == w2[1]) and w1 != w2:
            G.add_edge(w1, w2)
            edge_count += 1

print(f"{edge_count} edges added.")

max_set, found_cliques = networkx.approximation.clique_removal(G)

print(f"Maximum Independent Set: {max_set}")
print(f"Found Cliques: {found_cliques}")