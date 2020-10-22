# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
"""SDC category management module."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from onapsdk.configuration import settings
from onapsdk.sdc import SDC
from onapsdk.utils.headers_creator import headers_sdc_generic


class BaseCategory(SDC, ABC):  # pylint: disable=too-many-instance-attributes
    """Base SDC category class.

    It's SDC admin resource, has no common properties with
        SDC resourcer or elements, so SDC class can't be it's
        base class.

    """

    SDC_ADMIN_USER = "demo"

    def __init__(self, name: str) -> None:
        """Service category initialization.

        Args:
            name (str): Service category name.

        """
        super().__init__(name)
        self.normalized_name: str = None
        self.unique_id: str = None
        self.icons: List[str] = None
        self.subcategories: List[Dict[str, str]] = None
        self.version: str = None
        self.owner_id: str = None
        self.empty: bool = None
        self.type: str = None

    @classmethod
    def _get_all_url(cls) -> str:
        """Get URL for all categories in SDC."""
        return f"{cls.base_front_url}/sdc1/feProxy/rest/v1/setup/ui"

    @classmethod
    def _base_url(cls) -> str:
        """Give back the base url of Sdc."""
        return f"{settings.SDC_FE_URL}/sdc1/feProxy/rest/v1/category"

    @classmethod
    def import_from_sdc(cls, values: Dict[str, Any]) -> 'BaseCategory':
        """
        Import category object from SDC.

        Args:
            values (Dict[str, Any]): dict to parse returned from SDC.

        """
        category_obj = cls(name=values["name"])
        category_obj.normalized_name = values["normalizedName"]
        category_obj.unique_id = values["uniqueId"]
        category_obj.icons = values["icons"]
        category_obj.subcategories = values["subcategories"]
        category_obj.version = values["version"]
        category_obj.owner_id = values["ownerId"]
        category_obj.empty = values["empty"]
        return category_obj

    @classmethod
    @abstractmethod
    def category_name(cls) -> str:
        """Class category name.

        Used for logs.

        Returns:
            str: Category name

        """

    @classmethod
    def get(cls, name: str) -> "BaseCategory":
        """Get category with given name.

        Raises:
            ValueError: Category with given name does not exist

        Returns:
            BaseCategory: BaseCategory instance

        """
        category_obj: "BaseCategory" = cls(name)
        if category_obj.exists():
            return category_obj
        raise ValueError(f"{cls.category_name()} with \"{name}\" name does not exist")

    @classmethod
    def create(cls, name: str) -> "BaseCategory":
        """Create category instance.

        Checks if category with given name exists and if it already
            exists just returns category with given name.

        Raises:
            ValueError: Creation error

        Returns:
            BaseCategory: Created category instance

        """
        category_obj: "BaseCategory" = cls(name)
        if category_obj.exists():
            return category_obj
        cls.send_message_json("POST",
                              f"Create {name} {cls.category_name()}",
                              cls._base_create_url(),
                              data=json.dumps({"name": name}),
                              headers=headers_sdc_generic(cls.headers, user=cls.SDC_ADMIN_USER),
                              exception=ValueError)
        category_obj.exists()
        return category_obj

    def _copy_object(self, obj: 'BaseCategory') -> None:
        """
        Copy relevant properties from object.

        Args:
            obj (SdcResource): the object to "copy"

        """
        self.name = obj.name
        self.normalized_name = obj.normalized_name
        self.unique_id = obj.unique_id
        self.icons = obj.icons
        self.subcategories = obj.subcategories
        self.version = obj.version
        self.owner_id = obj.owner_id
        self.empty = obj.empty


class ResourceCategory(BaseCategory):
    """Resource category class."""

    @classmethod
    def _get_objects_list(cls,
                          result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get list of resource categories.

        Args:
            result (List[Dict[str, Any]]): the result returned by SDC
                in a list of dicts

        Raises:
            KeyError: Invalid result dictionary

        """
        return result["categories"]["resourceCategories"]

    @classmethod
    def _base_create_url(cls) -> str:
        """Url to create resource category.

        Returns:
            str: Creation url

        """
        return f"{cls._base_url()}/resources"

    @classmethod
    def category_name(cls) -> str:
        """Resource category name.

        Used for logging.

        Returns:
            str: Resource category name

        """
        return "Resource Category"


class ServiceCategory(BaseCategory):
    """Service category class."""

    @classmethod
    def _get_objects_list(cls,
                          result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get list of service categories.

        Args:
            result (List[Dict[str, Any]]): the result returned by SDC
                in a list of dicts

        Raises:
            KeyError: Invalid result dictionary

        """
        return result["categories"]["serviceCategories"]

    @classmethod
    def _base_create_url(cls) -> str:
        """Url to create service category.

        Returns:
            str: Creation url

        """
        return f"{cls._base_url()}/services"

    @classmethod
    def category_name(cls) -> str:
        """Service category name.

        Used for logging.

        Returns:
            str: Service category name

        """
        return "Service Category"
