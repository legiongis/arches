"""
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from django.core.management.base import BaseCommand

from arches.app.utils.extensions import ExtensionManager


class Command(BaseCommand):
    """
    Commands for managing Arches functions

    """

    def add_arguments(self, parser):

        parser.add_argument(
            "extension_type",
            help="The type of extension to be managed. Valid types are stored in "\
                "utils.extensions.ExtensionManager().lookup."
        )
        parser.add_argument(
            "operation",
            choices=[
                "list",
                "register",
                "update",
                "unregister",
                "import",
            ]
        )
        parser.add_argument(
            "-s", "--source",
            help="path to extension details file",
        )
        parser.add_argument(
            "-n", "--name",
            help="name of extension"
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            default=False,
            help="Overwrite an extension that has already been registered."
        )
        parser.add_argument(
            "--details",
            action="store_true",
            default=False,
            help="Used with the list operation to print the full details of each extension."
        )

    def handle(self, *args, **options):

        em = ExtensionManager(
            extension_type=options['extension_type'],
            raise_errors=False,
        )
        print("")

        operation = options["operation"]
        overwrite = options["overwrite"]
        if operation == "update":
            print("update is DEPRECATED. Please use \"register\" with \"--overwrite\" next time.\n")
            operation = "register"
            overwrite = True

        if operation == "list":
            print(f"LIST {em.extension_type}s\n---")
            em.list_registered(details=options["details"])

        if operation == "register":
            print(f"REGISTER {em.extension_type} (overwrite={overwrite}) | {options['source']}\n")
            em.load_source(options["source"])
            em.print_details()
            em.register(overwrite=overwrite)

        # if options["operation"] == "update":
        #     print(f"UPDATE {em.extension_type} | {options['source']}\n")
        #     em.load_source(options["source"])
        #     em.print_details()
        #     em.update()

        if operation == "unregister":
            print(f"UNREGISTER {em.extension_type} | {options['name']}\n")
            em.unregister(options["name"])

        if operation == "import":
            print(f"IMPORT {em.extension_type} | {options['source']}\n")
            em.import_from_directory(options["source"], overwrite=options["overwrite"])
