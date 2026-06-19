import os
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations, product
from collections.abc import Iterable, Iterator
import string
import json
import re
import math
from tqdm import tqdm

FILE_PATH, _ = os.path.split(os.path.realpath(__file__))

with open(f'{FILE_PATH}/../data/flask_mods.json', "r", encoding='utf-8') as f:
            data = json.load(f)

prefix = ["^" + p["Name"].lower() for p in data if p["Prefix"] == True]

suffix = [s["Name"].lower() + "$" for s in data if s["Prefix"] == False]

for i, s in enumerate(suffix):
    if s.startswith("of the "):
        suffix[i] = s[5:]
    elif s.startswith("of "):
        suffix[i] = s[1:]

with open(f'{FILE_PATH}/../data/flask_bases.json', "r", encoding='utf-8') as f:
            bases = json.load(f)

bases = [b.lower() for b in bases]

affix = prefix + suffix

affix_and_bases = affix + bases

short_names = {}

def getShortName(long_name:str, affixes:list[str]) -> str:
    
    for size in range(1, len(long_name) + 1):
        for start in range(len(long_name) + 1 - size):
            sn = long_name[start:start + size]

            for a in affixes:
                if a != long_name and sn in a:
                    break
            else:
                # print(f"{sn}: {long_name}")
                return sn

for a in affix:
    short_names[a] = getShortName(a, affix_and_bases)



def getBasicRegexLength(wanted: set(str)) -> int:
    return len(wanted) - 1 + sum(map(len, [short_names[w] for w in wanted]))


def generateSubstrings(word:str, key_letters: Iterable[str]) -> Iterator[str]:
    
    kl = key_letters[:]

    for length in range(1, len(word)+1):
        for start in range(len(word)-length + 1):
            substring = word[start: start + length]
            wild_string = ""

            for c in substring:
                if c in kl or c in ["^", "$"]:
                    wild_string += c
                else:
                    wild_string += '.'

            if wild_string != '.' * len(substring):
                for wcv in generateWildcardVariants(wild_string):
                    yield wcv


def generateWildcardVariants(word:str) -> Iterator[str]:
    
    letter_locations = []

    for i, c in enumerate(word):
        if c not in  ['.', '^', '$']:
            letter_locations.append(i)
    
    for i in range(2**len(letter_locations)-1):
        result = word
        a = 0
        while 2 ** a <= i:
            if i & 2 ** a:
                result = result[:letter_locations[a]] + "." + result[letter_locations[a]+1:]
            a += 1
        result = result.replace('.' * 9, '.{9}')
        result = result.replace('.' * 8, '.{8}')
        result = result.replace('.' * 7, '.{7}')
        result = result.replace('.' * 6, '.{6}')
        result = result.replace('.' * 5, '.{5}')
        yield result


def findComboMatch(wanted: set[str], affix: Iterable[str]) -> str:

    lc = list(string.ascii_lowercase) + ["'", " "]
    key_letters = [l for l in lc if all(l in word for word in wanted)]

    if " " in key_letters and len(key_letters) < 4:
        return None

    keyword = min(wanted, key=len)

    max_len = getBasicRegexLength(wanted)

    unwanted = {u for u in affix if u not in wanted}

    possible_matches = generateSubstrings(keyword, key_letters)

    for p in possible_matches:
        if len(p) >= max_len:
            return None
        guess = "".join(p)
        if len(p) == 4:
            pass
        if all(re.search(guess, w) is not None for w in wanted) and all(re.search("".join(p), u) is None for u in unwanted):
            return guess

combos:dict[str,dict[str,tuple[str]]] = {}

for combo_size in range(2, 6):
    print(f"generating size {combo_size}.")
    prefix_combos = combinations(prefix, combo_size)

    tot = math.comb(len(prefix), combo_size)

    for pc in tqdm(prefix_combos, total=tot):
        result = findComboMatch(pc, affix)
        if result:
            # print(f"Found '{result}' for {pc}")
            combos[result] = {"affix": pc, "bases": tuple(b.replace(" flask", "") for b in bases if re.search(result, b) is None)}
            if combos[result]["bases"] == []:
                combos.pop(result)

    suffix_combos = combinations(suffix, combo_size)
    tot = math.comb(len(suffix), combo_size)

    for sc in tqdm(suffix_combos, total=tot):
        if sc[0].startswith("f bl") and sc[1].startswith("f bl"):
            pass
        result = findComboMatch(sc, affix)
        if result:
            # print(f"Found '{result}' for {sc}")
            combos[result] = {"affix": sc, "bases": tuple(b.replace(" flask", "") for b in bases if re.search(result, b) is None)}
            if combos[result]["bases"] == []:
                combos.pop(result)

    with open(f'{FILE_PATH}/../data/combos.json', "w", encoding='utf-8') as f:
        json.dump(combos, f)