from cmd2 import Cmd, Cmd2ArgumentParser, with_argparser, Choices
import re
import json
import sqlite3
import networkx
import os
import pyperclip

FILE_PATH, _ = os.path.split(os.path.realpath(__file__))

class TrackerCommands(Cmd):

    def __init__(self):
        history_file = f'{FILE_PATH}/../data/command_history.dat'
        super().__init__(persistent_history_file=history_file, persistent_history_length=1000)

        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()
        self.prompt = ">"
        self.debug = True

        result = db_cur.execute("SELECT value FROM prefix")

        if result:
            self.prefix = [a[0] for a in result.fetchall()]
        else:
            self.prefix = ["DATABASE_ERROR"]
        
        result = db_cur.execute("SELECT value FROM suffix")

        if result:
            self.suffix = [a[0] for a in result.fetchall()]
        else:
            self.suffix = ["DATABASE_ERROR"]

    
    def providePrefixes(self):
        return Choices.from_values(self.prefix)
    

    def provideSuffixes(self):
        return Choices.from_values(self.suffix)
    

    def provideBases(self):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        result = db_cur.execute("SELECT value FROM base")

        if result:
            bases = [a[0] for a in result.fetchall()]
        else:
            bases = ["DATABASE_ERROR"]

        return Choices.from_values(bases)
    

    def provideWantedPrefixes(self, arg_tokens, **kwargs):

        base = arg_tokens.get('base')
        suffix = arg_tokens.get('suffix')

        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        if base:
            base_id = getBaseIDFromDB(base[0], db_cur)

            if suffix:
                suffix_id, _, _ = getSuffixInfoFromDB(suffix[0], db_cur)
                result = db_cur.execute("""SELECT prefix.value FROM wanted
                                        INNER JOIN prefix ON wanted.prefix_id = prefix.id
                                        WHERE base_id = ? AND suffix_id = ?""", (base_id, suffix_id))
            else:
                result = db_cur.execute("""SELECT prefix.value FROM wanted
                                        INNER JOIN prefix ON wanted.prefix_id = prefix.id
                                        WHERE base_id = ?""", (base_id,))
        else:
            return Choices.from_values(self.prefix)

        if result:
            prefix = [a[0] for a in result.fetchall()]
        else:
            prefix = ["DATABASE_ERROR"]

        return Choices.from_values(prefix)
    

    def provideWantedSuffixes(self, arg_tokens, **kwargs):
        base = arg_tokens.get('base')
        prefix = arg_tokens.get('prefix')

        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        if base:
            base_id = getBaseIDFromDB(base[0], db_cur)

            if prefix:
                prefix_id, _, _ = getPrefixInfoFromDB(prefix[0], db_cur)
                result = db_cur.execute("""SELECT suffix.value FROM wanted
                                        INNER JOIN suffix ON wanted.suffix_id = suffix.id
                                        WHERE base_id = ? AND prefix_id = ?""", (base_id, prefix_id))
            else:
                result = db_cur.execute("""SELECT suffix.value FROM wanted
                                        INNER JOIN suffix ON wanted.suffix_id = suffix.id
                                        WHERE base_id = ?""", (base_id,))
        else:
            return Choices.from_values(self.suffix)

        if result:
            suffix = [a[0] for a in result.fetchall()]
        else:
            suffix = ["DATABASE_ERROR"]

        return Choices.from_values(suffix)


    def provideWantedBases(self):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        result = db_cur.execute("""SELECT base.value FROM wanted
                                   INNER JOIN base ON wanted.base_id = base.id""")

        if result:
            bases = [a[0] for a in result.fetchall()]
        else:
            bases = ["DATABASE_ERROR"]

        return Choices.from_values(bases)


    add_parser = Cmd2ArgumentParser(description="Add flasks to the list of wanted crafting results")
    add_parser.add_argument('base', help="Base of the item to add", choices_provider=provideBases)
    add_parser.add_argument('-p', '--prefix', required=True, help="Prefix of the item to add", choices_provider=providePrefixes)
    add_parser.add_argument('-s', '--suffix', required=True, help="Suffix of the item to add", choices_provider=provideSuffixes)
    add_parser.add_argument('-t', '--tier', action='store_true', help="Prevents auto-adding of higher tier mods")
    @with_argparser(add_parser)
    def do_add(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        prefix_id, prefix_grp, prefix_lvl = getPrefixInfoFromDB(args.prefix, db_cur)
        base_id = getBaseIDFromDB(args.base, db_cur)
        suffix_id, suffix_grp, suffix_lvl = getSuffixInfoFromDB(args.suffix, db_cur)

        if args.tier:
            if base_id and prefix_id and suffix_id:
                db_cur.execute("""INSERT INTO wanted (prefix_id, base_id, suffix_id) VALUES (?,?,?)
                                  ON CONFLICT DO NOTHING""", (prefix_id, base_id, suffix_id))
                db_conn.commit()
            else:
                self.poutput("Add Failed")
        else:
            if base_id and prefix_id and suffix_id:
                # Get the ids of all mods equal to or better than the mods specified in the arguments
                result = db_cur.execute("""SELECT id FROM prefix WHERE modgroup = ? AND level >= ?""", (prefix_grp, prefix_lvl))
                prefix_id = [p[0] for p in result.fetchall()]

                result = db_cur.execute("""SELECT id FROM suffix WHERE modgroup = ? AND level >= ?""", (suffix_grp, suffix_lvl))
                suffix_id = [s[0] for s in result.fetchall()]

                for p in prefix_id:
                    for s in suffix_id:
                        db_cur.execute("""INSERT INTO wanted (prefix_id, base_id, suffix_id) VALUES (?,?,?)
                                        ON CONFLICT DO NOTHING""", (p, base_id, s))
                db_conn.commit()
    

    fill_parser = Cmd2ArgumentParser(description="Add all flasks to the list of wanted crafting results")
    fill_parser.add_argument('base', help="Base of the items to add", choices_provider=provideBases)
    @with_argparser(fill_parser)
    def do_fill(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        base_id = getBaseIDFromDB(args.base, db_cur)

        result = db_cur.execute("""SELECT id FROM prefix""")
        prefix_id = [p[0] for p in result.fetchall()]

        result = db_cur.execute("""SELECT id FROM suffix""")
        suffix_id = [s[0] for s in result.fetchall()]

        for p in prefix_id:
            for s in suffix_id:
                db_cur.execute("""INSERT INTO wanted (prefix_id, base_id, suffix_id) VALUES (?,?,?)
                                ON CONFLICT DO NOTHING""", (p, base_id, s))
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
                result = db_cur.execute("""SELECT id FROM prefix WHERE modgroup = ? AND level <= ?""", (prefix_grp, prefix_lvl))
                prefix_id = [p[0] for p in result.fetchall()]

                result = db_cur.execute("""SELECT id FROM suffix WHERE modgroup = ? AND level <= ?""", (suffix_grp, suffix_lvl))
                suffix_id = [s[0] for s in result.fetchall()]

                for p in prefix_id:
                    for s in suffix_id:
                        db_cur.execute("""DELETE FROM wanted WHERE 
                                        prefix_id = ? AND
                                        base_id = ? AND
                                        suffix_id = ?""", (p, base_id, s))
                db_conn.commit()

    fill_parser = Cmd2ArgumentParser(description="Empty the list of wanted crafting results")
    fill_parser.add_argument('base', help="Base of the items to clear", choices_provider=provideBases)
    @with_argparser(fill_parser)
    def do_empty(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        base_id = getBaseIDFromDB(args.base, db_cur)
        db_cur.execute("""DELETE FROM wanted WHERE base_id = ?""", (base_id,))
        db_conn.commit()


    base_parser = Cmd2ArgumentParser()
    base_parser.add_argument('-a', '--add', help="Base to add", type=str)
    base_parser.add_argument('-d', '--delete', help="Base to delete", choices_provider=provideBases)
    base_parser.add_argument('-l', '--list', help="List bases", action='store_true')
    @with_argparser(base_parser)
    def do_base(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        if args.add:
            db_cur.execute('INSERT INTO base (value) VALUES (?) ON CONFLICT DO NOTHING', (args.add.lower(),))
            db_conn.commit()
        if args.delete:
            db_cur.execute('DELETE FROM base WHERE value = ?', (args.delete.lower(),))
            db_conn.commit()
        if args.list or not (args.add or args.delete):
            result = db_cur.execute("SELECT value FROM base")

            if result:
                base = [a[0].lower() for a in result.fetchall()]
            else:
                base = ["DATABASE_ERROR"]

            self.poutput("Bases:")
            self.poutput("------")
            for b in base:
                self.poutput(b)
            self.poutput("")


    wanted_parser = Cmd2ArgumentParser()
    wanted_parser.add_argument('-b', '--base', help="Base filter", type=str)
    wanted_parser.add_argument('-p', '--prefix', help="Prefix filter", type=str)
    wanted_parser.add_argument('-s', '--suffix', help="Suffix filter", type=str)
    wanted_parser.add_argument('-o', '--sort', help="Sort order of the output", choices=["base", "prefix", "suffix"])
    @with_argparser(wanted_parser)
    def do_wanted(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        result = db_cur.execute("""SELECT prefix.value, base.value, suffix.value FROM wanted
                                   INNER JOIN prefix ON wanted.prefix_id = prefix.id
                                   INNER JOIN base ON wanted.base_id = base.id
                                   INNER JOIN suffix ON wanted.suffix_id = suffix.id""")
        
        if result:
            items = result.fetchall()

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
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        base_id = getBaseIDFromDB(args.base, db_cur)

        result = db_cur.execute("""SELECT prefix.short, suffix.short FROM wanted
                                   INNER JOIN prefix ON wanted.prefix_id = prefix.id
                                   INNER JOIN suffix ON wanted.suffix_id = suffix.id
                                   WHERE base_id = ?""", (base_id,))
        
        if result:
            items = result.fetchall()

            if items:
                G = networkx.Graph()

                for i in items:
                    G.add_node((i[0], i[1]))
                
                for i1 in items:
                    for i2 in items:
                        if i1 != i2 and not G.has_edge(i1, i2) and (i1[0], i2[1]) in items and (i2[0], i1[1]) in items:
                            G.add_edge(i1, i2)
                
                _, found_cliques = networkx.approximation.clique_removal(G)

                regex_strings = []

                for c in found_cliques:
                    pfx = set()
                    sfx = set()

                    for flask in c:
                        pfx.add(flask[0])
                        sfx.add(flask[1])
                    
                    regex_strings.append(f"^({args.base}|{'|'.join(pfx)}).*(flask|{'|'.join(sfx)})$")

                final_regex = "|".join(regex_strings)
                self.poutput(f"{len(final_regex)} characters")

                # Test the regex to check for false positives and false negatives
                all_flasks = [f"{p} {args.base} flask {s}" for p in self.prefix for s in self.suffix]
                
                result = db_cur.execute("""SELECT prefix.value, base.value, suffix.value FROM wanted
                                           INNER JOIN prefix ON wanted.prefix_id = prefix.id
                                           INNER JOIN base ON wanted.base_id = base.id
                                           INNER JOIN suffix ON wanted.suffix_id = suffix.id""")
                
                if result:
                    items = result.fetchall()

                wanted_flasks = [f"{i[0]} {i[1]} flask {i[2]}" for i in items if i[1] == args.base]

                for f in all_flasks:
                    if f in wanted_flasks:
                        if not re.match(final_regex,f):
                            self.poutput(f"ERROR: Regex failed to match wanted flask {f}")
                    else:
                        if re.match(final_regex,f):
                            self.poutput(f"ERROR: Regex gives false positive on unwanted flask {f}")

                self.poutput(final_regex)
                pyperclip.copy(final_regex)

            else:
                self.poutput("No wanted flasks found for the given base")
        

    def do_export(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        result = db_cur.execute("""SELECT prefix.value, base.value, suffix.value FROM wanted
                                   INNER JOIN prefix ON wanted.prefix_id = prefix.id
                                   INNER JOIN base ON wanted.base_id = base.id
                                   INNER JOIN suffix ON wanted.suffix_id = suffix.id""")
        
        w = result.fetchall()

        wanted:list[dict[str,str]] = [{"prefix": item[0], "base": item[1], "suffix": item[2] } for item in w]

        with open(f'{FILE_PATH}/../data/export.json', "w", encoding='utf-8') as f:
            json.dump(wanted, f)
    
    
    def do_import(self, args):
        db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        db_cur = db_conn.cursor()

        with open(f'{FILE_PATH}/../data/export.json', "r", encoding='utf-8') as f:
            items = json.load(f)

        for i in items:
            db_cur.execute('INSERT INTO base (value) VALUES (?) ON CONFLICT DO NOTHING', (i["base"].lower(),))

            prefix_id, prefix_grp, prefix_lvl = getPrefixInfoFromDB(i["prefix"], db_cur)
            base_id = getBaseIDFromDB(i["base"], db_cur)
            suffix_id, suffix_grp, suffix_lvl = getSuffixInfoFromDB(i["suffix"], db_cur)

            if base_id and prefix_id and suffix_id:
                db_cur.execute("""INSERT INTO wanted (prefix_id, base_id, suffix_id) VALUES (?,?,?)
                                  ON CONFLICT DO NOTHING""", (prefix_id, base_id, suffix_id))
        
        db_conn.commit()


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