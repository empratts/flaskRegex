#!/usr/bin/env python3

import json
import os
import re


FILE_PATH, _ = os.path.split(os.path.realpath(__file__))

with open(f'{FILE_PATH}/../data/flask_mod_poedb.json', "r", encoding='utf-8') as f:
    data = json.load(f)

affixes: list[dict] = data["normal"]


results = []

for a in affixes:
    item = {}
    item["Name"] = a.get("Name", "NAME NOT FOUND: ERROR")
    item["Level"] = int(a.get("Level", -1))
    item["Prefix"] = a.get("ModGenerationTypeID") == "1"

    str_match = re.match(r"<span class='mod-value'>\((\d+).*</span>(\d+)\)</span>(.*)<br><span class='mod-value'>(\d*)</span>(.*)$", a.get("str", ""))

    if str_match:
        item["String"] = f"{str_match.group(3)}  {str_match.group(4)}{str_match.group(5)}"
        item["Min"] = float(str_match.group(1))
        item["Max"] = float(str_match.group(2))

        results.append(item)
    else:
        str_match = re.match(r"<span class='mod-value'>.*\((\d+).*</span>(\d+)\)</span>(.*)$", a.get("str", ""))
        if str_match:
            item["String"] = f"{str_match.group(3)}"
            item["Min"] = float(str_match.group(1))
            item["Max"] = float(str_match.group(2))


            results.append(item)
        else:
            str_match = re.match(r".*<span class='mod-value'>((?:[01]\.)?\d+)</span>(.*)$", a.get("str", ""))

            if str_match:
                item["String"] = f"{str_match.group(2)}"
                item["Min"] = float(str_match.group(1))
                item["Max"] = float(str_match.group(1))


                results.append(item)
            else:
                print(f"No Match on {item["Name"]}")

print(f"{len(results)} of {len(affixes)} Found.")

affix_types = set()
for r in results:
    affix_types.add(r["String"])

print(f"{len(affix_types)} unique affix types found.")


with open(f'{FILE_PATH}/../data/flask_mods.json', "w", encoding='utf-8') as f:
    json.dump(results, f)