import os
import sys
import json
import signal
import sqlite3
import command

FILE_PATH, _ = os.path.split(os.path.realpath(__file__))

def setupDatabase():

    db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
    db_cur = db_conn.cursor()

    db_cur.execute("CREATE TABLE IF NOT EXISTS settings(name varchar(255), value varchar(255), UNIQUE(name))")

    initialized = db_cur.execute("SELECT value FROM settings WHERE name='initialized'")
    
    if not initialized:
        print("Database Error.")
        sys.exit(1)

    if len(initialized.fetchall()) == 0:
            
        db_cur.execute("CREATE TABLE IF NOT EXISTS prefix (id INTEGER PRIMARY KEY, value varchar(255), short varchar(255), modgroup INTEGER, level INTEGER, UNIQUE(value))")
        db_cur.execute("CREATE TABLE IF NOT EXISTS base (id INTEGER PRIMARY KEY, value varchar(255), UNIQUE(value))")
        db_cur.execute("CREATE TABLE IF NOT EXISTS suffix (id INTEGER PRIMARY KEY, value varchar(255), short varchar(255), modgroup INTEGER, level INTEGER, UNIQUE(value))")

        db_cur.execute("""CREATE TABLE IF NOT EXISTS wanted(
                          id INTEGER PRIMARY KEY,
                          prefix_id INTEGER NOT NULL,
                          base_id INTEGER NOT NULL,
                          suffix_id INTEGER NOT NULL,
                          FOREIGN KEY (prefix_id) REFERENCES prefix(id),
                          FOREIGN KEY (base_id) REFERENCES base(id),
                          FOREIGN KEY (suffix_id) REFERENCES suffix(id),
                          CONSTRAINT prefix_base_suffix UNIQUE (prefix_id, base_id, suffix_id))""")
        
        with open(f'{FILE_PATH}/../data/flask_mods.json', "r", encoding='utf-8') as f:
            affix = json.load(f)

        p_name = [p["Name"].lower() for p in affix if p["Prefix"] == True]
        p_group = [p["Group"] for p in affix if p["Prefix"] == True]
        p_level = [p["Level"] for p in affix if p["Prefix"] == True]

        s_name = [s["Name"].lower() for s in affix if s["Prefix"] == False]
        s_group = [s["Group"] for s in affix if s["Prefix"] == False]
        s_level = [s["Level"] for s in affix if s["Prefix"] == False]

        p_short = []
        
        for pn in p_name:
            for i in range(1, len(pn)):
                short = pn[:i]
                for full in p_name:
                    if full.startswith(short) and pn != full:
                        break
                else:
                    p_short.append(short)
                    break
            else:
                print(f"ERROR: Failed to find short name for {pn}.")
                p_short.append("")
        
        s_short = []

        for sn in s_name:
            for i in range(1, len(sn) + 1):
                short = sn[-i:]
                for full in s_name:
                    if full.endswith(short) and sn != full:
                        break
                else:
                    s_short.append(short)
                    break
            else:
                print(f"ERROR: Failed to find short name for {sn}.")
                s_short.append("")

        if len(p_name) != len(p_short) or len(s_name) != len(s_short):
            print("Failed calculating short names.")
            sys.exit(2)

        prefix = [p for p in zip(p_name, p_short, p_group, p_level)]
        suffix = [s for s in zip(s_name, s_short, s_group, s_level)]

        for p in prefix:
            db_cur.execute('INSERT INTO prefix (value, short, modgroup, level) VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING', p)
        
        for s in suffix:
            db_cur.execute('INSERT INTO suffix (value, short, modgroup, level) VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING', s)

        db_cur.execute("""INSERT INTO settings (name, value) VALUES("initialized", "Valid") ON CONFLICT DO NOTHING""")
        db_conn.commit()

def main():

    setupDatabase()

    def handler(_,__):
        sys.exit(0)

    signal.signal(signal.SIGINT, handler=handler)

    # Start the app here
    app = command.TrackerCommands()
    app.cmdloop()


if __name__ == "__main__":
    main()