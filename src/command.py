from cmd2 import Cmd, Cmd2ArgumentParser, with_argparser, Choices
import re
import json
import sqlite3
import os

FILE_PATH, _ = os.path.split(os.path.realpath(__file__))

class TrackerCommands(Cmd):

    def __init__(self):
        super().__init__()

        self.db_conn = sqlite3.connect(f'{FILE_PATH}/../data/item.db')
        self.db_cur = self.db_conn.cursor()
        self.prompt = ">"
    
    def providePrefixes(self):
        return Choices.from_values(["Prefix"])
    
    def provideSuffixes(self):
        return Choices.from_values(["Suffix"])
    
    def provideBases(self):
        return Choices.from_values(["Base"])

    add_parser = Cmd2ArgumentParser()
    add_parser.add_argument('base', help="Base of the item to add", choices_provider=provideBases)
    add_parser.add_argument('-p', '--prefix', required=True, help="Prefix of the item to add", choices_provider=providePrefixes)
    add_parser.add_argument('-s', '--suffix', required=True, help="Suffix of the item to add", choices_provider=provideSuffixes)

    @with_argparser(add_parser)
    def do_add(self, args):
        pass