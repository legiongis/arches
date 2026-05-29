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

import sys
import uuid

from arches.app.models import models
from arches.management.commands import utils
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """
    Commands for managing Arches search components

    """

    def add_arguments(self, parser):
        parser.add_argument("operation", nargs="?")

        parser.add_argument(
            "-s",
            "--source",
            action="store",
            dest="source",
            default="",
            help="Search Component json file or string to be loaded",
        )

        parser.add_argument(
            "-n",
            "--name",
            action="store",
            dest="name",
            default="",
            help="The js component name of the search component",
        )

    def handle(self, *args, **options):
        if options["operation"] == "register":
            self.register(source=options["source"])

        if options["operation"] == "unregister":
            self.unregister(name=options["name"])

        if options["operation"] == "list":
            self.list()

        if options["operation"] == "update":
            self.update(source=options["source"])

    def register(self, source):
        """
        Inserts a search component into the arches db. If enabled=True,
        insert this comonponent into the standard search configs.
        """

        utils.load_source("sc_source", source)
        if sys.modules.get("sc_source"):
            details = sys.modules["sc_source"].details

            try:
                uuid.UUID(details["searchcomponentid"])
            except (KeyError, ValueError):
                details["searchcomponentid"] = str(uuid.uuid4())
            print(
                "Registering the search component, %s, with componentid: %s"
                % (details["name"], details["searchcomponentid"])
            )

            layoutSortorder = details.get("layoutSortorder", 1)
            enabled = details.get("enabled")

            instance = models.SearchComponent(
                searchcomponentid=details["searchcomponentid"],
                name=details["name"],
                icon=details["icon"],
                modulename=details["modulename"],
                classname=details["classname"],
                type=details["type"],
                componentpath=details["componentpath"],
                componentname=details["componentname"],
            )

            instance.save()

            if enabled:

                standard_search = models.SearchComponent.objects.get(
                    componentname="standard-search-view"
                )
                filters = sorted(
                    standard_search.config["linkedSearchFilters"],
                    key=lambda x: x["layoutSortorder"]
                )
                filters.insert(layoutSortorder-1, {
                    "componentname": instance.componentname,
                    "searchcomponentid": instance.searchcomponentid,
                    "layoutSortorder": layoutSortorder,
                })
                # reset layout sorder to make it sequential
                for n, filter in enumerate(filters, start=1):
                    filter["layoutSortorder"] = n

                standard_search.config["linkedSearchFilters"] = filters
                standard_search.save()

    def update(self, source):
        """
        Updates an existing search component in the arches db

        """

        utils.load_source("sc_source", source)
        name = sys.modules["sc_source"].details["componentname"]

        self.unregister(name)
        self.register(source)

    def unregister(self, name):
        """
        Removes the search component from the system
        """

        try:
            instance = models.SearchComponent.objects.get(componentname=name)
            instance.delete()
        except Exception as e:
            print(e)

        # reset the standard search component configs to remove this filter
        standard_search = models.SearchComponent.objects.get(
            componentname="standard-search-view"
        )
        filters = [i for i in standard_search.config["linkedSearchFilters"]
                   if not i["componentname"] == name]
        filters.sort(key=lambda x: x["layoutSortorder"])

        # reset layout sorder to make it sequential
        for n, filter in enumerate(filters, start=1):
            filter["layoutSortorder"] = n

        standard_search.config["linkedSearchFilters"] = filters
        standard_search.save()

    def list(self):
        """
        Lists registered search components

        """

        try:
            instances = models.SearchComponent.objects.all()
            for instance in instances:
                print(instance.name)
        except Exception as e:
            print(e)
