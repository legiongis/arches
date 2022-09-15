from django.core.management.base import BaseCommand, CommandError

from arches.cli.utils import ArchesHelpTextFormatter, ArchesCLIStyles
from arches.cli.managers import ExtensionManager

s = ArchesCLIStyles()

class Command(BaseCommand):
    """
    Use this command to manage extensions within Arches.
    
    Usage:

        python manage.py extension [operation] [extension_type] [-s/--source] [-n/--name] [--overwrite]

    Operations:

        - list
        - register
        - unregister
        - activate
        - deactivate
    
    Use `list` for quick inspection of the database. If you need to supply a `--name` for an operation, use the value that is printed by the `list` operation.

    When you `register` an extension a new ORM instance is created. Add `--overwrite` update an existing instance based on the primary key of the extension defined in `--source`. Note: the name of the primary key field is different for every extension, but generally is something like "widgetid".

    Running `unregister` will delete the specified instance from the database.

    The `activate` and `deactivate` operations are only valid operations for a few different extension types. These actions alter an instance's `config['show']` value, but do not create or delete the instance. A deactivated extension will be hidden from the user interface but remain in the database. 

    Extension types:

        - card-component
        - datatype
        - etl-module
        - function
        - plugin --> use this for workflows
        - report
        - search-filter
        - widget

    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):

        parser.formatter_class = ArchesHelpTextFormatter

        parser.add_argument(
            "operation",
            choices=[
                "list",
                "register",
                "unregister",
                "activate",
                "deactivate",
            ],
            help=f"""OPERATION
            {s.req('list')}: List registered extensions of the specified type. The {s.opt('name')} of each extension is printed.
            {s.req('register')}: Register extension from source file (provide {s.opt('-s/--source')}).
            {s.req('unregister')}: Unregister the specified extension (provide {s.opt('-n/--name')}).
            {s.req('activate')}: Activate this extension (not available for all extension types) (provide {s.opt('-n/--name')}).
            {s.req('deactivate')}: Deactivate this extension but don't unregister it (not available for all extension types, experimental) (provide {s.opt('-n/--name')}).
            """
        )

        parser.add_argument(
            "extension_type",
            choices=[
                "card-component",
                "datatype",
                "etl-module",
                "function",
                "plugin",
                "report",
                "search-filter",
                "widget",
            ],
            help=f"""EXTENSION TYPE
            Specify what type of extension you are managing.
            """
        )

        parser.add_argument(
            "-s", "--source",
            help=f"Use with {s.req('register')} to provide a JSON or .py file when registering an extension.",
        )

        parser.add_argument(
            "-n", "--name",
            help=f"Use with {s.req('unregister')} for the name of the extension to remove."
        )

        parser.add_argument(
            "--overwrite",
            action="store_true",
            help=f"Use with {s.req('register')} to overwrite an existing extension with the provided source definition.",
        )

    def handle(self, *args, **options):

        ex = options["extension_type"]
        manager = ExtensionManager(extension_type=ex)

        # the list operation only makes sense in the context of the CLI,
        # so all code sits here, not in the manager.
        if options["operation"] == "list":
            try:
                instances = manager.model.objects.all()
                for n, instance in enumerate(instances, start=1):
                    if ex == "datatype":
                        name = instance.datatype
                    else:
                        name = instance.name
                    if ex in ["etl-module", "plugin"]:
                        name += f" ({'active' if instance.config['show'] is True else 'inactive'})"
                    # getting really carried away here
                    # name = s.req(name)
                    # if n % 2 == 0:
                    #     name = s.invert(name)
                    print(name)
                print(f"---\nregistered {ex} count: {instances.count()}")
            except Exception as e:
                print(s.error(e))
                raise e

        if options["operation"] == "register":
            print(f"Register {ex}: {options['source']} (overwrite = {options['overwrite']}")
            manager.register(options["source"], overwrite=options['overwrite'])

        if options["operation"] == "unregister":
            print(f"Unregister {ex}: {options['name']}")
            manager.unregister(options["name"])

        if options["operation"] == "activate":
            print(f"Activate {ex}: {options['name']}")
            manager.set_active(name=options["name"])

        if options["operation"] == "deactivate":
            print(s.warn("Warning: Deactivating core Arches extensions, like the Advanced "\
            "search filter, may cause unintended consequences."))
            print(f"Deactivate {ex}: {options['name']}")
            manager.set_active(name=options["name"], active=False)
