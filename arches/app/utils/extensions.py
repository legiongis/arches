import os
import uuid
import json
import importlib.util
from django.core import serializers
from arches.app.models.models import (
    CardComponent,
    DDataType,
    Function,
    Plugin,
    ReportTemplate,
    SearchComponent,
    Widget,
)

class ExtensionManager():

    def __init__(self, extension_type=None, raise_errors=True):

        self.lookup = {
            "card_component": {
                "model": CardComponent,
                "name_field": "name",
                "uuid_field": "componentid",
            },
            "datatype": {
                "model": DDataType,
                "name_field": "datatype",
                "uuid_field": "pk",
            },
            "function": {
                "model": Function,
                "name_field": "name",
                "uuid_field": "functionid",
            },
            "plugin": {
                "model": Plugin,
                "name_field": "name",
                "uuid_field": "pluginid",
            },
            "report": {
                "model": ReportTemplate,
                "name_field": "name",
                "uuid_field": "templateid",
            },
            "search": {
                "model": SearchComponent,
                "name_field": "name",
                "uuid_field": "searchcomponentid",
            },
            "widget": {
                "model": Widget,
                "name_field": "name",
                "uuid_field": "widgetid",
            },
        }

        if extension_type is not None:
            if not extension_type in self.lookup.keys():
                valid = ", ".join(list(self.lookup.keys()))
                raise(AttributeError(f"Invalid extension type. Choose from: {valid}"))

            self.extension_type = extension_type
            self.model = self.lookup[extension_type]["model"]
            self.name_field = self.lookup[extension_type]["name_field"]
            self.uuid_field = self.lookup[extension_type]["uuid_field"]
            self.source_path = ""
            self.details = {}

        self.raise_errors = raise_errors

    def load_source(self, source_path):

        ## load details from a python module (functions, datatypes)
        if source_path.endswith(".py"):
            try:
                spec = importlib.util.spec_from_file_location("", source_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            ## more precise exception handling would be good here
            except Exception as e:
                if self.raise_errors:
                    raise(e)
                else:
                    print(e)
            details = module.details

        ## load details form a json file (widgets, card_components, etc.)
        elif source_path.endswith(".json"):
            with open(source_path) as f:
                details = json.load(f)
        else:
            msg = "Invalid source path."
            if self.raise_errors:
                raise(OSError(msg))
            else:
                print(msg)
                exit()

        ## some extra work on the details...
        ## stuff like this, if there's a lot more of it, could be gathered in
        ## a self.sanitize_details() method or something.
        if self.extension_type in ["datatype", "function"]:
            details["modulename"] = os.path.basename(source_path)
        if self.extension_type == "datatype":
            details["issearchable"] = details.get("issearchable", False)
        ## every extension besides datatypes need to be registered with a uuid
        ## in a specific field, make sure that uuid is valid here.
        if self.extension_type != "datatype":
            try:
                uuid.UUID(details[self.uuid_field])
            except (ValueError, KeyError):
                details[self.uuid_field] = str(uuid.uuid4())

        self.details = details
        self.source_path = source_path

    def print_details(self):

        print("-"*80)
        print(f"{self.name_field}: {self.details[self.name_field]}")
        print(f"{self.uuid_field}: {self.details[self.uuid_field]}")
        print("-"*80)
        for k, v in self.details.items():
            if k not in [self.name_field, self.uuid_field]:
                print(f"{k} {(19-len(k))*' '}{v}")
        print("-"*80)

    def list_registered(self, details=False):
        """
        Lists registered extensions of a specified type.
        """

        try:
            instances = self.model.objects.all().order_by(self.name_field)
            for instance in instances:
                print(getattr(instance, self.name_field))
                if details is True:
                    data = json.loads(serializers.serialize('json', [instance]))
                    print(json.dumps(data[0]["fields"], indent=1))
        except Exception as e:
            if self.raise_errors:
                raise(e)
            else:
                print(e)

    def register(self, overwrite=False):
        """
        Registers a new extension in the database based on the provided source.
        """

        query = {self.name_field: self.details[self.name_field]}
        if self.model.objects.filter(**query).exists():
            if overwrite is True:
                return self.update()
            else:
                if self.raise_errors:
                    raise(Exception(f"{self.extension_type} {self.details[self.name_field]} already exists"))
                else:
                    print(f"""
This {self.extension_type} is already registered. You can overwrite it with

    python manage.py extension {self.extension_type} register -s {self.source_path} --overwrite
""")
                    exit()

        if self.extension_type == "card_component":
            instance = self.model(
                componentid=self.details["componentid"],
                name=self.details["name"],
                description=self.details["description"],
                component=self.details["component"],
                componentname=self.details["componentname"],
                defaultconfig=self.details["defaultconfig"],
            )
        elif self.extension_type == "datatype":
            instance = self.model(
                datatype=self.details["datatype"],
                iconclass=self.details["iconclass"],
                modulename=self.details["modulename"],
                classname=self.details["classname"],
                defaultwidget=self.details["defaultwidget"],
                defaultconfig=self.details["defaultconfig"],
                configcomponent=self.details["configcomponent"],
                configname=self.details["configname"],
                isgeometric=self.details["isgeometric"],
                issearchable=self.details["issearchable"],
            )
        elif self.extension_type == "function":
            instance = self.model(
                functionid=self.details["functionid"],
                name=self.details["name"],
                functiontype=self.details["type"],
                description=self.details["description"],
                defaultconfig=self.details["defaultconfig"],
                modulename=self.details["modulename"],
                classname=self.details["classname"],
                component=self.details["component"],
            )
        elif self.extension_type == "plugin":
            instance = self.model(
                pluginid=self.details["pluginid"],
                name=self.details["name"],
                icon=self.details["icon"],
                component=self.details["component"],
                componentname=self.details["componentname"],
                config=self.details["config"],
                slug=self.details["slug"],
                sortorder=self.details["sortorder"],
            )
        elif self.extension_type == "report":
            instance = self.model(
                templateid=self.details["templateid"],
                name=self.details["name"],
                description=self.details["description"],
                component=self.details["component"],
                componentname=self.details["componentname"],
                defaultconfig=self.details["defaultconfig"],
            )
        elif self.extension_type == "search":
            instance = self.model(
                searchcomponentid=self.details["searchcomponentid"],
                name=self.details["name"],
                icon=self.details["icon"],
                modulename=self.details["modulename"],
                classname=self.details["classname"],
                type=self.details["type"],
                componentpath=self.details["componentpath"],
                componentname=self.details["componentname"],
                sortorder=self.details["sortorder"],
                enabled=self.details["enabled"],
            )
        elif self.extension_type == "widget":
            instance = self.model(
                widgetid=self.details["widgetid"],
                name=self.details["name"],
                datatype=self.details["datatype"],
                helptext=self.details["helptext"],
                defaultconfig=self.details["defaultconfig"],
                component=self.details["component"],
            )
        instance.save()

    def update(self):
        """
        Updates an existing extension in the database.
        """

        query = {self.name_field: self.details[self.name_field]}
        try:
            instance = self.model.objects.get(**query)
        except self.model.DoesNotExist as e:
            if self.raise_errors:
                raise(e)
            else:
                print(f"""
This {self.extension_type} is not registered. Register it with

    python manage.py extension {self.extension_type} register -s {self.source_path}
""")

        if self.extension_type == "card_component":
            instance.description = self.details["description"]
            instance.component = self.details["component"]
            instance.componentname = self.details["componentname"]
            instance.defaultconfig = self.details["defaultconfig"]
        elif self.extension_type == "datatype":
            instance.iconclass = self.details["iconclass"]
            instance.modulename = self.details["modulename"]
            instance.classname = self.details["classname"]
            instance.defaultwidget = self.details["defaultwidget"]
            instance.defaultconfig = self.details["defaultconfig"]
            instance.configcomponent = self.details["configcomponent"]
            instance.configname = self.details["configname"]
            instance.isgeometric = self.details["isgeometric"]
            instance.issearchable = self.details["issearchable"]
        elif self.extension_type == "function":
            if self.raise_errors:
                raise(NotImplementedError)
            else:
                print(f"Update {self.extension_type} not implemented.")
                exit()
        elif self.extension_type == "plugin":
            instance.icon = self.details["icon"]
            instance.component = self.details["component"]
            instance.componentname = self.details["componentname"]
            instance.config = self.details["config"]
        elif self.extension_type == "report":
            if self.raise_errors:
                raise(NotImplementedError)
            else:
                print(f"Update {self.extension_type} not implemented.")
                exit()
        elif self.extension_type == "search":
            if self.raise_errors:
                raise(NotImplementedError)
            else:
                print(f"Update {self.extension_type} not implemented.")
                exit()
        elif self.extension_type == "widget":
            instance.datatype = self.details["datatype"]
            instance.helptext = self.details["helptext"]
            instance.defaultconfig = self.details["defaultconfig"]
            instance.component = self.details["component"]

        instance.save()

    def unregister(self, name):
        """
        Removes an extension of the specified type from the database.
        """
        try:
            query = {self.name_field: name}
            instance = self.model.objects.get(**query)
            instance.delete()
        except self.model.DoesNotExist as e:
            if self.raise_errors:
                raise(e)
            else:
                print(f"""
This {self.extension_type} is not registered. List registered {self.extension_type}s with

    python manage.py extension {self.extension_type} list
""")
