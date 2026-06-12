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

random.seed(1)

edge_count = 0
for p in p_names:
    for s in s_names:
        if random.randint(0,99) < 20:
            G.add_edge(p, s)
            edge_count += 1
            # print(f"{p} Flask {s}")

print(f"{edge_count} edges added.")

for i in range(2, 9):
    print(f"{i} of {len(p_names)}")
    comb = combinations(p_names, i)
    found = 0
    order = 0
    for c in comb:
        common:set = None
        for pfx in c:
            if common is None:
                common = set(G.neighbors(pfx))
            else:
                common.intersection_update(set(G.neighbors(pfx)))
            if common == set([]):
                break
        else:
            # print(f"{c} all share the suffixes {common}.")
            found += 1
            order = max(order, len(common))
            # break
    if found == 0:
        print(f"No group of size {i} found.")
        break
    else:
        print(f"{found} groups of size {i} with max order {order}.")

groups:list[dict[tuple,set]] = [{(p,) : set(G.neighbors(p)) for p in p_names}]
singles = groups[0]

while len(groups[-1]) > 0:
    new_group = {}
    order = 0
    for k, v in groups[-1].items():
        for pfx, sfxs in singles.items():
            if pfx not in k:
                new_item = set(k)
                new_item.add(pfx)
                new_sfxs:set = v.intersection(sfxs)
                if len(new_sfxs) > 0:
                    new_group[tuple(new_item)] = new_sfxs
                    order = max(order, len(new_sfxs))
    groups.append(new_group)
    print(f"{len(new_group)} items found with max order {order}")
