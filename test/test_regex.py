import pytest
import os
import sys
import re
import random

from .context import TrackerCommands

def test_basic():
    base = "jade"

    wanted_flasks_for_base = {("bottomless", "of bog moss"), ("bottomless", "of incision"), ("bottomless", "of penetrating"), ("bottomless", "of plume moss"), ("bottomless", "of tenaciousness"), ("bottomless", "of the antelope"), ("bottomless", "of the armadillo"), ("bottomless", "of the cheetah"), ("bottomless", "of the curlew"), ("bottomless", "of the ibex"), ("bottomless", "of the impala"), ("bottomless", "of the kakapo"), ("bottomless", "of the kaleidoscope"), ("bottomless", "of the lynx"), ("bottomless", "of the owl"), ("bottomless", "of the pangolin"), ("bottomless", "of the rainbow"), ("brewer's", "of bog moss"), ("brewer's", "of plume moss"), ("brewer's", "of tenaciousness"), ("brewer's", "of the antelope"), ("brewer's", "of the armadillo"), ("brewer's", "of the cheetah"), ("brewer's", "of the ibex"), ("brewer's", "of the impala"), ("brewer's", "of the kakapo"), ("brewer's", "of the kaleidoscope"), ("brewer's", "of the lynx"), ("brewer's", "of the owl"), ("brewer's", "of the pangolin"), ("brewer's", "of the rainbow"), ("chemist's", "of bog moss"), ("chemist's", "of plume moss"), ("chemist's", "of tenaciousness"), ("chemist's", "of the antelope"), ("chemist's", "of the armadillo"), ("chemist's", "of the cheetah"), ("chemist's", "of the ibex"), ("chemist's", "of the impala"), ("chemist's", "of the kakapo"), ("chemist's", "of the kaleidoscope"), ("chemist's", "of the lynx"), ("chemist's", "of the owl"), ("chemist's", "of the pangolin"), ("chemist's", "of the rainbow"), ("clinician's", "of the cheetah"), ("clinician's", "of the lynx"), ("experimenter's", "of the bear"), ("experimenter's", "of the cheetah"), ("experimenter's", "of the lynx"), ("flagellant's", "of bog moss"), ("flagellant's", "of incision"), ("flagellant's", "of penetrating"), ("flagellant's", "of plume moss"), ("flagellant's", "of rupturing"), ("flagellant's", "of tenaciousness"), ("flagellant's", "of the antelope"), ("flagellant's", "of the armadillo"), ("flagellant's", "of the beluga"), ("flagellant's", "of the cheetah"), ("flagellant's", "of the crystal"), ("flagellant's", "of the curlew"), ("flagellant's", "of the gazelle"), ("flagellant's", "of the ibex"), ("flagellant's", "of the impala"), ("flagellant's", "of the kakapo"), ("flagellant's", "of the kaleidoscope"), ("flagellant's", "of the lynx"), ("flagellant's", "of the mockingbird"), ("flagellant's", "of the owl"), ("flagellant's", "of the pangolin"), ("flagellant's", "of the rainbow"), ("flagellant's", "of the seal"), ("masochist's", "of bog moss"), ("masochist's", "of incision"), ("masochist's", "of penetrating"), ("masochist's", "of plume moss"), ("masochist's", "of rupturing"), ("masochist's", "of tenaciousness"), ("masochist's", "of the antelope"), ("masochist's", "of the armadillo"), ("masochist's", "of the beluga"), ("masochist's", "of the cheetah"), ("masochist's", "of the crystal"), ("masochist's", "of the curlew"), ("masochist's", "of the gazelle"), ("masochist's", "of the ibex"), ("masochist's", "of the impala"), ("masochist's", "of the kakapo"), ("masochist's", "of the kaleidoscope"), ("masochist's", "of the lynx"), ("masochist's", "of the mockingbird"), ("masochist's", "of the owl"), ("masochist's", "of the pangolin"), ("masochist's", "of the rainbow"), ("masochist's", "of the seal"), ("perpetual", "of bog moss"), ("perpetual", "of incision"), ("perpetual", "of penetrating"), ("perpetual", "of plume moss"), ("perpetual", "of tenaciousness"), ("perpetual", "of the antelope"), ("perpetual", "of the armadillo"), ("perpetual", "of the cheetah"), ("perpetual", "of the curlew"), ("perpetual", "of the ibex"), ("perpetual", "of the impala"), ("perpetual", "of the kakapo"), ("perpetual", "of the kaleidoscope"), ("perpetual", "of the lynx"), ("perpetual", "of the owl"), ("perpetual", "of the pangolin"), ("perpetual", "of the rainbow"), ("transgressor's", "of bog moss"), ("transgressor's", "of incision"), ("transgressor's", "of penetrating"), ("transgressor's", "of plume moss"), ("transgressor's", "of rupturing"), ("transgressor's", "of tenaciousness"), ("transgressor's", "of the antelope"), ("transgressor's", "of the armadillo"), ("transgressor's", "of the beluga"), ("transgressor's", "of the cheetah"), ("transgressor's", "of the crystal"), ("transgressor's", "of the curlew"), ("transgressor's", "of the gazelle"), ("transgressor's", "of the ibex"), ("transgressor's", "of the impala"), ("transgressor's", "of the kakapo"), ("transgressor's", "of the kaleidoscope"), ("transgressor's", "of the lynx"), ("transgressor's", "of the mockingbird"), ("transgressor's", "of the owl"), ("transgressor's", "of the pangolin"), ("transgressor's", "of the rainbow"), ("transgressor's", "of the seal"),}
    found_cliques = TrackerCommands.computeCliques(wanted_flasks_for_base)

    regex_strings:list[str] = []

    for clique in found_cliques:
        reg = TrackerCommands.genRegexForClique(clique, base)
        regex_strings.append(reg)

    final_regex = "|".join(regex_strings)

    all_flasks = [f"{p} {base} flask {s}" for p in TrackerCommands.prefix for s in TrackerCommands.suffix]
            
    wanted_flask_strings = {f"{w[0]} {base} flask {w[1]}" for w in wanted_flasks_for_base}

    for f in all_flasks:
        if f in wanted_flask_strings:
            assert re.search(final_regex,f) is not None
        else:
            assert re.search(final_regex,f) is None

def test_combos():
    base = "jade"

    for combo, combo_affixes in TrackerCommands.combos.items():
        
        wanted_flasks_for_base = set()

        if "^" in combo_affixes[0]:
            # Prefix

            # Add these prefixes with some random suffixes
            suf = random.sample(list(TrackerCommands.suffix), k=4)

            wanted_flasks_for_base = {(p[1:], s) for p in combo_affixes for s in suf}
        else:
            # Suffix

            # Add these suffixes with some random prefixes
            pre = random.sample(list(TrackerCommands.prefix), k=4)

            wanted_flasks_for_base = {(p, s[:-1]) for s in combo_affixes for p in pre}
    
        # Add 100 other random flasks from a pool of 400

        prefix_pool = random.sample(list(TrackerCommands.prefix), k=20)
        suffix_pool = random.sample(list(TrackerCommands.suffix), k=20)
        flask_pool = [(p, s) for p in prefix_pool for s in suffix_pool]

        flask_sample = random.sample(flask_pool, k = 100)

        for f in flask_sample:
            wanted_flasks_for_base.add(f)

        found_cliques = TrackerCommands.computeCliques(wanted_flasks_for_base)

        regex_strings:list[str] = []

        for clique in found_cliques:
            reg = TrackerCommands.genRegexForClique(clique, base)
            regex_strings.append(reg)

        final_regex = "|".join(regex_strings)

        all_flasks = [f"{p} {base} flask {s}" for p in TrackerCommands.prefix for s in TrackerCommands.suffix]
                
        wanted_flask_strings = {f"{w[0]} {base} flask {w[1]}" for w in wanted_flasks_for_base}

        for f in all_flasks:
            if f in wanted_flask_strings:
                assert re.search(final_regex,f) is not None
            else:
                assert re.search(final_regex,f) is None
