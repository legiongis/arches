import json

from django.core.management.base import BaseCommand, CommandError

from arches.cli.managers import ExtensionManager
from arches.cli.utils import ArchesHelpTextFormatter, ArchesCLIStyles

s = ArchesCLIStyles()

class Command(BaseCommand):
    """
    Run ETL modules from the command line instead of through a browser.

    Usage:

        python manage.py etl [module_name] [method_name] [--opts arg1=val1 arg2=val2]

    A rudimentary and generic implementation so far, allows you to run a specific method on a ETL module, passing in keyword arguments as needed. This can be used during the development of ETL modules, or later to run server-side ETL operations that mimic the functionality available through the browser.
    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):
        parser.formatter_class = ArchesHelpTextFormatter
        parser.add_argument("module_name",
            help=f"Name of ETL module to use. Use {s.fg.pink}python manage.py extension list etl-module{s.reset} to get a list of valid ETL module names. Remember to use quotes around names that contain spaces."
        )
        parser.add_argument("method_name",
            help='Name of method on ETL module class to run.'
        )
        parser.add_argument("--opts",
            nargs='*',
            help=f"Pass arbitrary keyword arguments to the method. Use format {s.opt('--opts arg1=val1 arg2=val2')}"
        )

    def handle(self, *args, **options):

        try:
            opts = {}
            for i in options['opts']:
                k, v = i.split("=")
                if v == "True":
                    v = True
                elif v == "False":
                    v = False
                opts[k] = v
        except Exception as e:
            print(s.error(options['opts']))
            print(s.warn("Invalid opts list. Format must be --opts arg1=val1 arg2=val2"))
            exit()

        self.run_method(options['module_name'], options['method_name'], **opts)

    def print_module_list(self):
        ExtensionManager("etl-module").print_list()

    def run_method(self, module_name, method_name, **kwargs):

        try:
            instance = ExtensionManager("etl-module")._get_instance(module_name)
        except Exception as e:
            print(s.error(e))
            print(s.warn("Valid module names:"))
            self.print_module_list()
            exit()

        module_class = instance.get_class_module()
        module = module_class()
        try:
            method = getattr(module, method_name)
        except AttributeError as e:
            print(s.error(e))
            print(s.warn("Invalid method name."))
            exit()
        
        result = method(**kwargs)
        if isinstance(result, dict):
            print(json.dumps(result, indent=2))
        else:
            print(result)
