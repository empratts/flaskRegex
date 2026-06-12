import json
import networkx
import re
import os
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

base = "Jade Flask"

flasks = []

for p in prefix:
    for s in suffix:
        full_name = f"{p} {base} {s}"
        flasks.append(full_name)

print(f"{len(flasks)} unique flask conbinations")


G = networkx.Graph()
G.add_nodes_from(p_names)
G.add_nodes_from(s_names)

# add edges between all prefixes
# p_edges = [ (a, b) for a in p_names for b in p_names if a != b]
# G.add_edges_from(p_edges)

# s_edges = [ (a, b) for a in s_names for b in s_names if a != b]
# G.add_edges_from(s_edges)

G.add_edge("Transgressor's", "of the Impala")
G.add_edge("Transgressor's", "of the Ibex")
G.add_edge("Transgressor's", "of the Rainbow")
G.add_edge("Transgressor's", "of the Kaleidoscope")

G.add_edge("Masochist's", "of the Impala")
G.add_edge("Masochist's", "of the Ibex")
G.add_edge("Masochist's", "of the Rainbow")
G.add_edge("Masochist's", "of the Kaleidoscope")

G.add_edge("Flagellant's", "of the Impala")
G.add_edge("Flagellant's", "of the Ibex")
G.add_edge("Flagellant's", "of the Rainbow")
G.add_edge("Flagellant's", "of the Kaleidoscope")

for i in range(2, len(p_names)):
    print(f"{i} of {len(p_names)}")
    comb = combinations(p_names, i)
    for c in comb:
        for p1, p2 in zip(c, c):
            p1_n = set(G.neighbors(p1))
            p2_n = set(G.neighbors(p2))
            if p1_n == set() or p1_n != p2_n:
                break
        else:
            print(f"{c} all share the suffixes {p1_n}.")
            break
    else:
        print(f"No group of size {i} found.")
        break

