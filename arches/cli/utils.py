import uuid
import textwrap
from argparse import RawTextHelpFormatter

from django.db.models.functions import Lower

from arches.app.models.graph import Graph

class ArchesCLIStyles():
    '''Styles for Arches CLI output. Borrowed heavily from https://stackoverflow.com/a/26445590/3873885.

    Usage:

        s = ArchesCLIStyles()

    Add arbitrary style within strings:

        print(f"{s.fg.red}Red text{s.reset} not red text")

    Some methods transform text in predetermined ways, like the following format for an optional CLI argument:

        print(s.opt("--source"))

    **Further notes**

    Reset all colors with s.reset
    Two subclasses fg for foreground and bg for background.
    Use as s.subclass.colorname.
        i.e. s.fg.red or s.bg.green
    Also, the generic bold, disable, underline, reverse, strikethrough,
    and invisible work with the main class
        i.e. s.bold
    '''
    reset='\033[0m'
    bold='\033[01m'
    disable='\033[02m'
    underline='\033[04m'
    blink='\33[5m'
    noblink='\33[25m'
    reverse='\033[07m'
    strikethrough='\033[09m'
    invisible='\033[08m'
    class fg:
        black='\033[30m'
        red='\033[31m'
        green='\033[32m'
        orange='\033[33m'
        blue='\033[34m'
        purple='\033[35m'
        cyan='\033[36m'
        lightgrey='\033[37m'
        darkgrey='\033[90m'
        lightred='\033[91m'
        lightgreen='\033[92m'
        yellow='\033[93m'
        lightblue='\033[94m'
        pink='\033[95m'
        lightcyan='\033[96m'
    class bg:
        black='\033[40m'
        red='\033[41m'
        green='\033[42m'
        orange='\033[43m'
        blue='\033[44m'
        purple='\033[45m'
        cyan='\033[46m'
        lightgrey='\033[47m'
        salmon='\033[101m'

    def print_ansi_codes(self):
        """
        This is a helper method that may be useful during style development.

        https://stackoverflow.com/a/39452138/3873885
        """
        x  = 0
        for i in range(24):
            colors = ""
            for j in range(5):
                code = str(x+j)
                colors += "\33[" + code + "m\\33[" + code + "m\033[0m "
            print(colors)
            x += 5

    def req(self, string):
        return f"{self.fg.lightgreen}{string}{self.reset}"

    def opt(self, string):
        return f"{self.fg.yellow}{string}{self.reset}"

    def invert(self, string):
        return f"{self.reverse}{string}{self.reset}"

    def error(self, string):
        return f"{self.fg.lightred}{self.bold}{self.blink}{string}{self.reset}"

    def warn(self, string):
        return f"{self.fg.cyan}{self.bold}{string}{self.reset}"

class ArchesHelpTextFormatter(RawTextHelpFormatter):
    def _split_lines(self, text, width):
        ret = []
        for line in text.splitlines():
            ret += [i for i in textwrap.wrap(line.strip(), width)]
        return ret

def get_graph(name_or_uuid):

    graph = None
    try:
        uid = uuid.UUID(str(name_or_uuid))
    except ValueError:
        qs = Graph.objects.annotate(name_lower=Lower('name'))
        graphs = qs.filter(name_lower=str(name_or_uuid).lower(), isresource=True)
        if graphs.count() == 1:
            return graphs[0]
        elif graphs.count() > 1:
            msg = "Choose one of the following (by number):"
            lookup = {}
            for n, g in enumerate(graphs, start=1):
                msg += f"\n{n}. {g.name}, {g.uuid}"
                lookup[n] = g
            choice = input(msg)
            if choice in lookup:
                graph = lookup[choice]

    return graph


