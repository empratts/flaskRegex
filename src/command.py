from cmd2 import Cmd, Cmd2ArgumentParser, with_argparser, Choices
from collections.abc import Iterable
from itertools import combinations
import re
import json
import sqlite3
import networkx
import os
import pyperclip
import asyncio
import signal

FILE_PATH, _ = os.path.split(os.path.realpath(__file__))

def sig_handler(signum, frame):
    raise TimeoutError("Timeout")

class TrackerCommands(Cmd):

    def __init__(self):
        history_file = f'{FILE_PATH}/../data/command_history.dat'
        super().__init__(persistent_history_file=history_file, persistent_history_length=1000)

        signal.signal(signal.SIGALRM, sig_handler)

        self.wanted_flasks_for_base: set[tuple[str,str]] = set()
        self.found_cliques: list[set[tuple[str,str]]] = []
        self.wanted_affixes: set[str] = set()

        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()
        self.prompt = ">"
        self.debug = True

        with open(f'{FILE_PATH}/../data/combos.json', "r", encoding='utf-8') as f:
            self.combos = json.load(f)

        wanted_flasks = db_cur.execute("""SELECT prefix.value, base.value, suffix.value FROM wanted
                                   INNER JOIN prefix ON wanted.prefix_id = prefix.id
                                   INNER JOIN base ON wanted.base_id = base.id
                                   INNER JOIN suffix ON wanted.suffix_id = suffix.id""")

        if wanted_flasks:
            self.wanted_flasks:set[tuple[str,str,str]] = set(wanted_flasks.fetchall())
        else:
            self.wanted_flasks:set[tuple[str,str,str]] = set()
            self.poutput("ERROR: Failed getting wanted flasks from database!")
        
        wanted_bases = db_cur.execute("SELECT value FROM base")

        if wanted_bases:
            self.wanted_bases:set[str] = {a[0].lower() for a in wanted_bases.fetchall()}
        else:
            self.wanted_bases:set[str] = {"DATABASE_ERROR"}
        

        prefix = db_cur.execute("SELECT value FROM prefix")

        if prefix:
            self.prefix:set[str] = {a[0] for a in prefix.fetchall()}
        else:
            self.prefix:set[str] = {"DATABASE_ERROR"}
        
        suffix = db_cur.execute("SELECT value FROM suffix")

        if suffix:
            self.suffix:set[str] = {a[0] for a in suffix.fetchall()}
        else:
            self.suffix:set[str] = {"DATABASE_ERROR"}

        with open(f'{FILE_PATH}/../data/flask_bases.json', "r", encoding='utf-8') as f:
            bases:list[str] = json.load(f)

        self.bases:set[str] = {b.lower().replace(" flask", "") for b in bases}

    
    def providePrefixes(self):
        return Choices.from_values(self.prefix)
    

    def provideSuffixes(self):
        return Choices.from_values(self.suffix)
    

    def provideUnwantedBases(self):
        unwanted_bases = self.bases.difference(self.wanted_bases)
        return Choices.from_values(unwanted_bases)
    
    
    def provideWantedBases(self):
        return Choices.from_values(self.wanted_bases)
    

    def provideWantedPrefixes(self, arg_tokens, **kwargs):

        base = arg_tokens.get('base')
        suffix = arg_tokens.get('suffix')

        if base:
            if suffix:
                result:set[str] = {w[0] for w in self.wanted_flasks if w[1] == base[0] and w[2] == suffix[0]}
            else:
                result:set[str] = {w[0] for w in self.wanted_flasks if w[1] == base[0]}
        else:
            result:set[str] = {w[0] for w in self.wanted_flasks}

        return Choices.from_values(result)
    

    def provideWantedSuffixes(self, arg_tokens, **kwargs):
        base = arg_tokens.get('base')
        prefix = arg_tokens.get('prefix')

        if base:

            if prefix:
                result:set[str] = {w[2] for w in self.wanted_flasks if w[1] == base[0] and w[0] == prefix[0]}
            else:
                result:set[str] = {w[2] for w in self.wanted_flasks if w[1] == base[0]}
        else:
            result:set[str] = {w[2] for w in self.wanted_flasks}

        return Choices.from_values(result)


    add_parser = Cmd2ArgumentParser(description="Add flasks to the list of wanted crafting results")
    add_parser.add_argument('base', help="Base of the item to add", choices_provider=provideWantedBases)
    add_parser.add_argument('-p', '--prefix', required=True, help="Prefix of the item to add", choices_provider=providePrefixes)
    add_parser.add_argument('-s', '--suffix', required=True, help="Suffix of the item to add", choices_provider=provideSuffixes)
    add_parser.add_argument('-t', '--tier', action='store_true', help="Prevents auto-adding of higher tier mods")
    add_parser.add_argument('-a', '--aggressive', action='store_true', help="Forces auto-adding of all tiers of the prefix and suffix mods")
    @with_argparser(add_parser)
    def do_add(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        prefix_id, prefix_grp, prefix_lvl = getPrefixInfoFromDB(args.prefix, db_cur)
        base_id = getBaseIDFromDB(args.base, db_cur)
        suffix_id, suffix_grp, suffix_lvl = getSuffixInfoFromDB(args.suffix, db_cur)

        if args.tier:
            if base_id and prefix_id and suffix_id:
                self.wanted_flasks.add((args.prefix, args.base, args.suffix))
                db_cur.execute("""INSERT INTO wanted (prefix_id, base_id, suffix_id) VALUES (?,?,?)
                                  ON CONFLICT DO NOTHING""", (prefix_id, base_id, suffix_id))
                db_conn.commit()
            else:
                self.poutput("Add Failed")
        else:
            if base_id and prefix_id and suffix_id:
                # Get the ids of all mods equal to or better than the mods specified in the arguments
                if args.aggressive:
                    prefix_lvl = 0
                    suffix_lvl = 0
                result = db_cur.execute("""SELECT id, value FROM prefix WHERE modgroup = ? AND level >= ?""", (prefix_grp, prefix_lvl))
                prefixes = [p for p in result.fetchall()]

                result = db_cur.execute("""SELECT id, value FROM suffix WHERE modgroup = ? AND level >= ?""", (suffix_grp, suffix_lvl))
                suffixes = [s for s in result.fetchall()]

                for p_id, p_value in prefixes:
                    for s_id, s_value in suffixes:
                        self.wanted_flasks.add((p_value, args.base, s_value))
                        db_cur.execute("""INSERT INTO wanted (prefix_id, base_id, suffix_id) VALUES (?,?,?)
                                        ON CONFLICT DO NOTHING""", (p_id, base_id, s_id))
                db_conn.commit()
    

    fill_parser = Cmd2ArgumentParser(description="Add all flasks to the list of wanted crafting results")
    fill_parser.add_argument('base', help="Base of the items to add", choices_provider=provideWantedBases)
    @with_argparser(fill_parser)
    def do_fill(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        base_id = getBaseIDFromDB(args.base, db_cur)

        result = db_cur.execute("""SELECT id, value FROM prefix""")
        prefixes = [p for p in result.fetchall()]

        result = db_cur.execute("""SELECT id, value FROM suffix""")
        suffixes = [s for s in result.fetchall()]

        for p_id, p_value in prefixes:
            for s_id, s_value in suffixes:
                self.wanted_flasks.add((p_value, args.base, s_value))
                db_cur.execute("""INSERT INTO wanted (prefix_id, base_id, suffix_id) VALUES (?,?,?)
                                ON CONFLICT DO NOTHING""", (p_id, base_id, s_id))
        db_conn.commit()


    remove_parser = Cmd2ArgumentParser()
    remove_parser.add_argument('base', help="Base of the item to add", choices_provider=provideWantedBases)
    remove_parser.add_argument('-p', '--prefix', required=True, help="Prefix of the item to add", choices_provider=provideWantedPrefixes)
    remove_parser.add_argument('-s', '--suffix', required=True, help="Suffix of the item to add", choices_provider=provideWantedSuffixes)
    remove_parser.add_argument('-t', '--tier', action='store_true', help="Prevents auto-removing of lower tier mods")
    @with_argparser(remove_parser)
    def do_remove(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        prefix_id, prefix_grp, prefix_lvl = getPrefixInfoFromDB(args.prefix, db_cur)
        base_id = getBaseIDFromDB(args.base, db_cur)
        suffix_id, suffix_grp, suffix_lvl = getSuffixInfoFromDB(args.suffix, db_cur)

        if args.tier:
            if base_id and prefix_id and suffix_id:
                self.wanted_flasks.remove((args.prefix, args.base, args.suffix))
                db_cur.execute("""DELETE FROM wanted WHERE
                                prefix_id = ? AND
                                base_id = ? AND
                                suffix_id = ?""", (prefix_id, base_id, suffix_id))
                db_conn.commit()
            else:
                self.poutput("Remove Failed")
        else:
            if base_id and prefix_id and suffix_id:
                # Get the ids of all mods equal to or worse than the mods specified in the arguments
                result = db_cur.execute("""SELECT id, value FROM prefix WHERE modgroup = ? AND level <= ?""", (prefix_grp, prefix_lvl))
                prefixes = [p for p in result.fetchall()]

                result = db_cur.execute("""SELECT id, value FROM suffix WHERE modgroup = ? AND level <= ?""", (suffix_grp, suffix_lvl))
                suffixes = [s for s in result.fetchall()]

                for p_id, p_value in prefixes:
                    for s_id, s_value in suffixes:
                        self.wanted_flasks.discard((p_value, args.base, s_value))
                        db_cur.execute("""DELETE FROM wanted WHERE 
                                        prefix_id = ? AND
                                        base_id = ? AND
                                        suffix_id = ?""", (p_id, base_id, s_id))
                db_conn.commit()

    fill_parser = Cmd2ArgumentParser(description="Empty the list of wanted crafting results")
    fill_parser.add_argument('base', help="Base of the items to clear", choices_provider=provideWantedBases)
    @with_argparser(fill_parser)
    def do_empty(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        if args.base:
            # sync in memory
            self.wanted_flasks = {w for w in self.wanted_flasks if w[1] != args.base}
            # sync in database
            base_id = getBaseIDFromDB(args.base, db_cur)
            db_cur.execute("""DELETE FROM wanted WHERE base_id = ?""", (base_id,))
        else:
            # sync in memory
            self.wanted_flasks = set()
            # sync in database
            db_cur.execute("""DELETE FROM wanted""")

        db_conn.commit()


    base_parser = Cmd2ArgumentParser()
    base_parser.add_argument('-a', '--add', help="Base to add", choices_provider=provideUnwantedBases)
    base_parser.add_argument('-d', '--delete', help="Base to delete", choices_provider=provideWantedBases)
    base_parser.add_argument('-l', '--list', help="List wanted bases", action='store_true')
    @with_argparser(base_parser)
    def do_base(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        if args.add:
            self.wanted_bases.add(args.add)
            db_cur.execute('INSERT INTO base (value) VALUES (?) ON CONFLICT DO NOTHING', (args.add.lower(),))
            db_conn.commit()
            self.bases
        if args.delete:
            self.wanted_bases.remove(args.delete)
            db_cur.execute('DELETE FROM base WHERE value = ?', (args.delete.lower(),))
            db_conn.commit()
        if args.list or not (args.add or args.delete):

            self.poutput("Bases:")
            self.poutput("------")
            for b in self.wanted_bases:
                self.poutput(b)
            self.poutput("")


    wanted_parser = Cmd2ArgumentParser()
    wanted_parser.add_argument('-b', '--base', help="Base filter", choices_provider=provideWantedBases)
    wanted_parser.add_argument('-p', '--prefix', help="Prefix filter", choices_provider=provideWantedPrefixes)
    wanted_parser.add_argument('-s', '--suffix', help="Suffix filter", choices_provider=provideWantedSuffixes)
    wanted_parser.add_argument('-o', '--sort', help="Sort order of the output", choices=["base", "prefix", "suffix"])
    @with_argparser(wanted_parser)
    def do_wanted(self, args):

        items = [w for w in self.wanted_flasks]
        
        if args.sort:
            if args.sort == "prefix":
                items.sort()
            if args.sort == "base":
                items.sort(key=lambda x: x[1])
            if args.sort == "suffix":
                items.sort(key=lambda x: x[2])

        if args.prefix:
            items = [i for i in items if i[0] == args.prefix]
        if args.base:
            items = [i for i in items if i[1] == args.base]
        if args.suffix:
            items = [i for i in items if i[2] == args.suffix]

        self.poutput(f"{len(items)} wanted items:")
        self.poutput("----------------")
        for i in items:
            self.poutput(f"{i[0]} {i[1]} flask {i[2]}")
    

    regex_parser = Cmd2ArgumentParser()
    regex_parser.add_argument('base', help="Base of the item to generate regex for", choices_provider=provideWantedBases)
    @with_argparser(regex_parser)
    def do_regex(self, args):

        self.genWatnedFlasksForBase(args.base)

        if self.wanted_flasks_for_base:

            self.computeCliques()

            regex_strings = []

            for clique in self.found_cliques:

                reg = self.genRegexForClique(clique, args.base)
                
                regex_strings.append(reg)

            final_regex = "|".join(regex_strings)

            # Test the regex to check for false positives and false negatives
            all_flasks = [f"{p} {args.base} flask {s}" for p in self.prefix for s in self.suffix]
            
            wanted_flask_strings = {f"{w[0]} {args.base} flask {w[1]}" for w in self.wanted_flasks_for_base}

            for f in all_flasks:
                if f in wanted_flask_strings:
                    if not re.search(final_regex,f):
                        self.poutput(f"ERROR: Regex failed to match wanted flask: {f}")
                else:
                    if re.search(final_regex,f):
                        self.poutput(f"ERROR: Regex gives false positive on unwanted flask: {f}")

            self.poutput(f"{len(final_regex)} characters")
            final_regex = '"' + final_regex + '"'
            self.poutput(final_regex)
            pyperclip.copy(final_regex)

        else:
            self.poutput("No wanted flasks found for the given base")
        

    def do_export(self, args):

        wanted:list[dict[str,str]] = [{"prefix": item[0], "base": item[1], "suffix": item[2] } for item in self.wanted_flasks]

        with open(f'{FILE_PATH}/../data/export.json', "w", encoding='utf-8') as f:
            json.dump(wanted, f)
    

    def do_import(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        with open(f'{FILE_PATH}/../data/export.json', "r", encoding='utf-8') as f:
            items = json.load(f)

        for i in items:
            db_cur.execute('INSERT INTO base (value) VALUES (?) ON CONFLICT DO NOTHING', (i["base"].lower(),))
            self.wanted_bases.add(i["base".lower()])

            prefix_id, prefix_grp, prefix_lvl = getPrefixInfoFromDB(i["prefix"], db_cur)
            base_id = getBaseIDFromDB(i["base"], db_cur)
            suffix_id, suffix_grp, suffix_lvl = getSuffixInfoFromDB(i["suffix"], db_cur)

            if base_id and prefix_id and suffix_id:
                self.wanted_flasks.add((i["prefix"], i["base"], i["suffix"]))
                db_cur.execute("""INSERT INTO wanted (prefix_id, base_id, suffix_id) VALUES (?,?,?)
                                  ON CONFLICT DO NOTHING""", (prefix_id, base_id, suffix_id))
        
        db_conn.commit()


    def genWatnedFlasksForBase(self, base:str):
        self.wanted_flasks_for_base = {(w[0], w[2]) for w in self.wanted_flasks if w[1] == base}

    
    def computeCliques(self):

        G = networkx.Graph()

        for i in self.wanted_flasks_for_base:
            G.add_node((i[0], i[1]))
        
        for i1 in self.wanted_flasks_for_base:
            for i2 in self.wanted_flasks_for_base:
                if i1 != i2 and not G.has_edge(i1, i2) and (i1[0], i2[1]) in self.wanted_flasks_for_base and (i2[0], i1[1]) in self.wanted_flasks_for_base:
                    G.add_edge(i1, i2)
        
        self.found_cliques = []

        try:
            signal.setitimer(signal.ITIMER_REAL, 0.5)
            _, self.found_cliques = networkx.approximation.clique_removal(G)
            pass
        except TimeoutError, RecursionError:
            # cancel the alarm, in case we get here because of the RecursionError before the alarm fired
            signal.alarm(0)
            self.poutput("Clique removal failed. Falling back to greedy clique finding.")
            # greedy approach when clique_removal fails
            while G.number_of_nodes() > 0:
                # start with the node with the most edges
                degree_sorted_nodes = list(G.degree)
                degree_sorted_nodes.sort(key = lambda x:x[1], reverse=True)

                fc:set[tuple[str,str]] = {degree_sorted_nodes[0][0]}
                
                # Greedy add of nodes in decreasing degree order
                for node, degree in degree_sorted_nodes:
                    if node not in fc and all(G.has_edge(node, n) for n in fc):
                        fc.add(node)
                
                self.found_cliques.append(fc)

                G.remove_nodes_from(fc)
        finally:
            # Cancel the alarm
            signal.alarm(0)


    def genRegexForClique(self, clique:set[str], base: str) -> str:

        self.poutput("Making regex for clique.")
        pfx = set()
        sfx = set()

        for flask in clique:
            pfx.add("^" + flask[0])
            sfx.add(flask[1] + "$")

        self.wanted_affixes = pfx.union(sfx)

        affixes = [f"^{p}" for p in self.prefix] + [f"{s}$" for s in self.suffix]

        base_short_name = getBaseShortName(base, affixes)

        valid_prefix_combos:dict[str,list[str]] = {}
        valid_suffix_combos:dict[str,list[str]] = {}
        for combo, criteria in self.combos.items():
            if base in criteria["bases"] and all(affix in pfx for affix in criteria["affix"]):
                valid_prefix_combos[combo] = criteria["affix"]
            if base in criteria["bases"] and all(affix in sfx for affix in criteria["affix"]):
                valid_suffix_combos[combo] = criteria["affix"]

        self.poutput(f"Found {len(valid_prefix_combos)} valid prefix combos and {len(valid_suffix_combos)} valid suffix combos.")

        p_group = self.optimizeGroup(pfx, base, base_short_name, affixes, valid_prefix_combos)
        s_group = self.optimizeGroup(sfx, base, "sk$", affixes, valid_suffix_combos)

        return f"({p_group}).*({s_group})"


    def getBestCombo(self, group:set[str], base: str, base_regex:str, affix_list:list[str], valid_combos:dict[str,list[str]]) -> (str, list[str]):
        
        best_combo = None
        best_remaining_names = []
        short_names = [getShortName(f, affix_list, base) for f in group] + [base_regex]
        best_option = min([foldPrefix(short_names), foldSuffix(short_names)], key=len)

        for combo, affixes in valid_combos.items():
            remaining_names = [affix for affix in group if affix not in affixes]
            short_names = [getShortName(f, affix_list, base) for f in remaining_names] + [base_regex]
            new_option = min([f"{combo}|{foldPrefix(short_names)}", f"{combo}|{foldSuffix(short_names)}"], key=len)
            best_option = min([new_option, best_option], key=len)
            if best_option == new_option:
                best_combo = combo
                best_remaining_names = remaining_names
        
        return (best_combo, best_remaining_names)
            

    def optimizeGroup(self, group:set[str], base: str, base_regex:str, affix_list:list[str], valid_combos:dict[str,list[str]]) -> str:
        results:list[str] = []
        remaining_names = group

        while True:
            new_combo, new_remaining_names = self.getBestCombo(remaining_names, base, base_regex, affix_list, valid_combos)
            if new_combo:
                results.append(new_combo)
                remaining_names = new_remaining_names
            else:
                break

        short_names = [getShortName(f, affix_list, base) for f in remaining_names]

        best_fold = min([foldPrefix(short_names), foldSuffix(short_names)], key=len)
        
        return f"{"|".join(results)}|{best_fold}"


def getBaseIDFromDB(value:str, db_cur:sqlite3.Cursor) -> int:
    result = db_cur.execute("SELECT id FROM base WHERE value = ?", (value,))
    if result:
        r = result.fetchone()
        if r:
            return r[0]
    return None


def getPrefixInfoFromDB(value:str, db_cur:sqlite3.Cursor) -> int:
    result = db_cur.execute("SELECT id, modgroup, level FROM prefix WHERE value = ?", (value,))
    if result:
        return result.fetchone()
    return None


def getSuffixInfoFromDB(value:str, db_cur:sqlite3.Cursor) -> int:
    result = db_cur.execute("SELECT id, modgroup, level FROM suffix WHERE value = ?", (value,))
    if result:
         return result.fetchone()       
    return None


def getShortName(long_name:str, affixes:list[str], base:str) -> str:
    
    for size in range(1, len(long_name) + 1):
        for start in range(len(long_name) + 1 - size):
            sn = long_name[start:start + size]

            if sn in base:
                continue

            for a in affixes:
                if a != long_name and sn in a:
                    break
            else:
                # print(f"{sn}: {long_name}")
                return sn

def getBaseShortName(long_name:str, affixes:list[str]) -> str:
    long_name = "^" + long_name
    afx = "%".join(affixes)
    for size in range(1, len(long_name) + 1):
        sn = long_name[:size]
        if sn not in afx:
            return sn
    return None

def generateGroup(words: Iterable[str]) -> str:
    options = ["|".join(words)]

    options.append(foldPrefix(words))
    options.append(foldSuffix(words))

    # print(options)

    return min(options, key=len)


def foldPrefix(words: Iterable[str]) -> str:
    folds:dict[str, list[str]] = {}

    for word in words:
        if word[0] in folds:
            folds[word[0]].append(word[1:])
        else:
            folds[word[0]] = [word[1:]]
    
    short_words:list[str] = []

    for pfx, sfxs in folds.items():
        if len(sfxs) > 2:
            folded = f"{pfx}({'|'.join(sfxs)})"
            short_words.append(folded)
        elif len(sfxs) == 2:
            short_words.append(pfx+sfxs[1])
            short_words.append(pfx+sfxs[0])
        else:
            short_words.append(pfx+sfxs[0])
    
    return "|".join(short_words)

def foldSuffix(words: Iterable[str]) -> str:
    folds:dict[str, list[str]] = {}

    for word in words:
        if word[-1] in folds:
            folds[word[-1]].append(word[:-1])
        else:
            folds[word[-1]] = [word[:-1]]
    
    short_words:list[str] = []

    for sfx, pfxs in folds.items():
        if len(pfxs) > 2:
            folded = f"({'|'.join(pfxs)}){sfx}"
            short_words.append(folded)
        elif len(pfxs) == 2:
            short_words.append(pfxs[1]+sfx)
            short_words.append(pfxs[0]+sfx)
        else:
            short_words.append(pfxs[0]+sfx)
    
    return "|".join(short_words)

