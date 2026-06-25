from command import TrackerCommands

base = "jade"
wanted_flasks_for_base = {('wide', "analyst's"), ('constant', 'bountiful'), ('bountiful', "masochist's"), ('bottomless', "clinician's"), ('continuous', 'bountiful'), ("apprentice's", 'perpetual'), ("transgressor's", "surgeon's"), ('doled', "scholar's"), ('continuous', 'continuous'), ("practitioner's", 'perpetual'), ("doctor's", "alchemist's"), ("alchemist's", 'bountiful'), ("analyst's", "scholar's"), ('provisioned', 'ample'), ("practitioner's", "clinician's"), ("alchemist's", 'continuous'), ('bottomless', 'continuous'), ('constant', "scholar's"), ('provisioned', 'allocated'), ("investigator's", 'ample'), ('continuous', "analyst's"), ("dabbler's", "masochist's"), ("apprentice's", 'bountiful'), ("apprentice's", 'ample'), ('constant', 'abundant'), ("masochist's", "apprentice's"), ('bountiful', "surgeon's"), ("physician's", "scholar's"), ('provisioned', "scholar's"), ("investigator's", "apprentice's"), ("transgressor's", "practitioner's"), ("surgeon's", 'continuous'), ("physician's", 'abundant'), ('doled', 'continuous'), ('doled', 'constant'), ("analyst's", 'continuous'), ('bottomless', "surgeon's"), ("analyst's", 'constant'), ('doled', "medic's"), ('wide', "abecedarian's"), ('allocated', "apprentice's"), ("analyst's", "medic's"), ('doled', "abecedarian's"), ("apprentice's", "clinician's"), ('provisioned', "masochist's"), ("analyst's", "abecedarian's"), ('constant', "analyst's"), ('allocated', 'perpetual'), ("abecedarian's", "examiner's"), ("physician's", "practitioner's"), ("investigator's", 'constant'), ('continuous', "abecedarian's"), ('bottomless', "medic's"), ("dabbler's", "practitioner's"), ("examiner's", 'of the narwhal'), ("masochist's", "scholar's"), ("flagellant's", 'of the narwhal'), ('abundant', 'of the hare'), ("abecedarian's", 'ample'), ("abecedarian's", 'allocated'), ("masochist's", 'abundant'), ("dabbler's", "abecedarian's"), ('bountiful', 'allocated'), ("transgressor's", "examiner's"), ("dabbler's", "alchemist's"), ("practitioner's", "abecedarian's"), ("dabbler's", "experimenter's"), ('wide', "examiner's"), ("surgeon's", "abecedarian's"), ('allocated', 'of the narwhal'), ("dabbler's", 'allocated'), ('provisioned', "practitioner's"), ('constant', "abecedarian's"), ("abecedarian's", "clinician's"), ("transgressor's", "apprentice's"), ("analyst's", "experimenter's"), ("doctor's", 'continuous'), ('wide', 'allocated'), ("examiner's", 'of the hare'), ("doctor's", 'constant'), ('doled', 'ample'), ('provisioned', "abecedarian's"), ("physician's", "investigator's"), ("alchemist's", "examiner's"), ('bountiful', 'bountiful'), ("dabbler's", 'perpetual'), ("masochist's", "investigator's"), ("apprentice's", "medic's"), ("masochist's", "alchemist's"), ('wide', 'perpetual'), ('continuous', 'allocated'), ('bountiful', "apprentice's"), ('bottomless', 'ample'), ('allocated', 'of the hare'), ("doctor's", "surgeon's"), ('continuous', "apprentice's"), ("abecedarian's", 'abundant'), ("transgressor's", 'continuous'), ("analyst's", "examiner's"), ("transgressor's", 'constant'), ('constant', 'perpetual'), ("practitioner's", 'ample'), ('allocated', "experimenter's"), ('constant', "examiner's"), ('bottomless', "scholar's"), ("dabbler's", "scholar's"), ('abundant', 'of the narwhal'), ("flagellant's", 'of the hare')}

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