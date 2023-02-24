import os
import imp
import json
import uuid
import logging

from django.db import transaction
from django.contrib.gis.db.models import UUIDField

from arches.app.models import models
from arches.cli.utils import ArchesCLIStyles

logger = logging.getLogger(__name__)

class ExtensionManager():

    def __init__(self, extension_type=None):
        self.model_lookup = {
            "card-component": models.Widget,
            "datatype": models.DDataType,
            "etl-module": models.ETLModule,
            "function": models.Function,
            "plugin": models.Plugin,
            "report": models.ReportTemplate,
            "search-filter": models.SearchComponent,
            "widget": models.Widget,
        }

        self.extension_type = extension_type
        self.model = self._get_model(extension_type) if extension_type else None

    def _get_source_details(self, source_path, ensure_valid_uuid_pk=False):

        ## load details from a python module (functions, datatypes, etc.)
        if source_path.endswith(".py"):

            try:
                source = imp.load_source("", source_path)
            ## more precise exception handling would be good here
            except Exception as e:
                raise(e)
            details = source.details

        ## load details form a json file (widgets, card_components, etc.)
        elif source_path.endswith(".json"):

            with open(source_path) as f:
                details = json.load(f)
        else:
            raise Exception(f"Invalid source path: {source_path}")

        if ensure_valid_uuid_pk is True:
            details = self._ensure_valid_uuid_pk(details)

        return details

    def _ensure_valid_uuid_pk(self, details):

        if isinstance(self.model._meta.pk, UUIDField):
            val = details.get(self.model._meta.pk.name)
            try:
                uuid.UUID(val)
            except ValueError:
                details[self.model._meta.pk.name] = str(uuid.uuid4())
        return details

    def _get_model(self, extension_type):

        if extension_type in self.model_lookup:
            return self.model_lookup[extension_type]
        else:
            raise Exception(f"Extension type not supported: {extension_type}")

    def _get_instance(self, name):

        try:
            if self.extension_type == "datatype":
                instance = self.model.objects.get(datatype=name)
            else:
                instance = self.model.objects.get(name=name)
            return instance
        except self.model.DoesNotExist:
            raise Exception(f"Can't find {self.extension_type}: {name}")

    def register(self, source, overwrite=False):
        """
        Registers a new extension in the database based on the provided source
        """

        details = self._get_source_details(source, ensure_valid_uuid_pk=True)

        # pop the pk value so the details can be iterated later without it
        pk_field = self.model._meta.pk.name
        pk_val = details.pop(pk_field)
        pk_qry = {self.model._meta.pk.name: pk_val}

        with transaction.atomic():
            if overwrite is True and self.model.objects.filter(**pk_qry).exists():
                instance = self.model.objects.get(**pk_qry)
            else:
                try:
                    instance = self.model(**pk_qry)
                except Exception as e:
                    print(e)
                    raise e

            # some extensions are irregular and the details need to be altered a little bit
            # before they can be saved to the instance. Generally these attribute definitions
            # are taken from existing commands.
            if self.extension_type == "datatype":
                details['modulename'] = os.path.basename(source)
                details['issearchable'] = details.get("issearchable", False)
            if self.extension_type == "function":
                details['modulename'] = os.path.basename(source)
            if self.extension_type == "report":
                details['preload_resource_data'] = details.get("preload_resource_data", True)

            # finally, set the attributes from all of the details values
            for k, v in details.items():
                setattr(instance, k, v)

            try:
                instance.save()
            except Exception as e:
                logger.error(e)
                raise e

    def unregister(self, name):
        """
        Removes an extension of the specified type from the database
        """

        try:
            instance = self._get_instance(name)
            instance.delete()
        except Exception as e:
            logger.error(e)
            raise e

    def set_active(self, name, active=True):

        if self.extension_type in ["etl-module", "plugin"]:
            instance = self._get_instance(name)
            instance.config['show'] = active
            instance.save()
        elif self.extension_type == "search-filter":
            instance = self._get_instance(name)
            instance.enabled = active
            instance.save()
        else:
            logger.warn(f"This operation not supported for {self.extension_type}.")

    def print_list(self):
        s = ArchesCLIStyles()
        try:
            instances = self.model.objects.all()
            for n, instance in enumerate(instances, start=1):
                if self.extension_type == "datatype":
                    name = instance.datatype
                else:
                    name = instance.name
                # for certain extension types that can be disabled, prepend name with status
                active_str = f"{s.fg.green}active{s.reset}"
                inactive_str = f"{s.fg.red}inactive{s.reset}"
                if self.extension_type in ["etl-module", "plugin"]:
                    name = f"{active_str if instance.config['show'] is True else inactive_str} {name}"
                if self.extension_type in ["search-filter"]:
                    name = f"{active_str if instance.enabled is True else inactive_str} {name}"
                print(name)
            print(f"---\nregistered {self.extension_type} count: {instances.count()}")
        except Exception as e:
            print(s.error(e))
            raise e