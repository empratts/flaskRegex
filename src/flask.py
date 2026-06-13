import sys
import signal
import sqlite3
import command

FILE_PATH, _ = os.path.split(os.path.realpath(__file__))

def setupDatabase():

    db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
    db_cur = self.db_conn.cursor()
    
    db_cur.execute("CREATE TABLE IF NOT EXISTS prefix (id INTEGER PRIMARY KEY, value varchar(255), UNIQUE(value))")
    db_cur.execute("CREATE TABLE IF NOT EXISTS base (id INTEGER PRIMARY KEY, value varchar(255), UNIQUE(value))")
    db_cur.execute("CREATE TABLE IF NOT EXISTS suffix (id INTEGER PRIMARY KEY, value varchar(255), UNIQUE(value))")

    db_cur.execute("""CREATE TABLE IF NOT EXISTS wanted(
                id INTEGER PRIMARY KEY,
                prefix_id INTEGER NOT NULL,
                base_id INTEGER NOT NULL,
                suffix_id INTEGER NOT NULL,
                FOREIGN KEY (prefix_id) REFERENCES prefix(id),
                FOREIGN KEY (base_id) REFERENCES base(id),
                FOREIGN KEY (suffix_id) REFERENCES suffix(id))""")
    db_conn.commit()

def main():

    setupDatabase()

    def handler(_,__):
        sys.exit(0)

    signal.signal(signal.SIGINT, handler=handler)

    app = command.TrackerCommands()

    app.cmdloop()

    # Start the app here

if __name__ == "__main__":
    main()