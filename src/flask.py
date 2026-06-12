import sys
import signal
import sqlite3

def setupDatabase():
    pass

def main():

    setupDatabase()

    def handler(_,__):
        sys.exit(0)

    signal.signal(signal.SIGINT, handler=handler)

    # Start the app here

if __name__ == "__main__":
    main()