# coding: utf-8

"""
AskUI Workspaces API

No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

The version of the OpenAPI document: 0.1.30
Generated by OpenAPI Generator (https://openapi-generator.tech)

Do not edit the class manually.
"""  # noqa: E501

from __future__ import annotations

import json
import pprint
import re  # noqa: F401
from typing import Any, ClassVar, Dict, List, Optional, Set

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictStr,
    field_validator,
)
from typing_extensions import Annotated, Self

from askui.tools.askui.askui_workspaces.models.agent_create_command_data_destinations_inner import (
    AgentCreateCommandDataDestinationsInner,
)
from askui.tools.askui.askui_workspaces.models.email_agent_trigger_create import (
    EmailAgentTriggerCreate,
)
from askui.tools.askui.askui_workspaces.models.json_schema import JsonSchema


class AgentCreateCommand(BaseModel):
    """
    AgentCreateCommand
    """  # noqa: E501

    name: Annotated[str, Field(strict=True)] = Field(
        description="The name of the agent. The name must only contain the following characters: a-z, A-Z, 0-9, -, _, and space. The name must not be empty. The name must start and end with a letter or a number. The name must not be longer than 64 characters."
    )
    description: Optional[Annotated[str, Field(strict=True, max_length=1024)]] = ""
    data_schema: JsonSchema = Field(
        description="The JSON schema of the data that the agent is going to extract from documents uploaded. The schema must comply with Draft 2020-12. The schema (root) must be an object with at least one property. The size of the schema must not exceed 15 MB.",
        alias="dataSchema",
    )
    auto_confirm: Optional[StrictBool] = Field(
        default=False,
        description="If true, the agent will automatically confirm the data extracted, i.e., no review is necessary.",
        alias="autoConfirm",
    )
    data_destinations: Optional[List[AgentCreateCommandDataDestinationsInner]] = Field(
        default=None, alias="dataDestinations"
    )
    parent_id: Optional[StrictStr] = Field(default=None, alias="parentId")
    email_trigger: Optional[EmailAgentTriggerCreate] = Field(
        default=None, alias="emailTrigger"
    )
    workspace_id: StrictStr = Field(alias="workspaceId")
    additional_properties: Dict[str, Any] = {}
    __properties: ClassVar[List[str]] = [
        "name",
        "description",
        "dataSchema",
        "autoConfirm",
        "dataDestinations",
        "parentId",
        "emailTrigger",
        "workspaceId",
    ]

    @field_validator("name")
    def name_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-_.+ ]{0,62}[a-zA-Z0-9])?$", value):
            raise ValueError(
                r"must validate the regular expression /^[a-zA-Z0-9]([a-zA-Z0-9-_.+ ]{0,62}[a-zA-Z0-9])?$/"
            )
        return value

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        protected_namespaces=(),
    )

    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        # TODO: pydantic v2: use .model_dump_json(by_alias=True, exclude_unset=True) instead
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Optional[Self]:
        """Create an instance of AgentCreateCommand from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        * Fields in `self.additional_properties` are added to the output dict.
        """
        excluded_fields: Set[str] = set(
            [
                "additional_properties",
            ]
        )

        _dict = self.model_dump(
            by_alias=True,
            exclude=excluded_fields,
            exclude_none=True,
        )
        # override the default output from pydantic by calling `to_dict()` of data_schema
        if self.data_schema:
            _dict["dataSchema"] = self.data_schema.to_dict()
        # override the default output from pydantic by calling `to_dict()` of each item in data_destinations (list)
        _items = []
        if self.data_destinations:
            for _item in self.data_destinations:
                if _item:
                    _items.append(_item.to_dict())
            _dict["dataDestinations"] = _items
        # override the default output from pydantic by calling `to_dict()` of email_trigger
        if self.email_trigger:
            _dict["emailTrigger"] = self.email_trigger.to_dict()
        # puts key-value pairs in additional_properties in the top level
        if self.additional_properties is not None:
            for _key, _value in self.additional_properties.items():
                _dict[_key] = _value

        # set to None if parent_id (nullable) is None
        # and model_fields_set contains the field
        if self.parent_id is None and "parent_id" in self.model_fields_set:
            _dict["parentId"] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of AgentCreateCommand from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "name": obj.get("name"),
                "description": obj.get("description")
                if obj.get("description") is not None
                else "",
                "dataSchema": JsonSchema.from_dict(obj["dataSchema"])
                if obj.get("dataSchema") is not None
                else None,
                "autoConfirm": obj.get("autoConfirm")
                if obj.get("autoConfirm") is not None
                else False,
                "dataDestinations": [
                    AgentCreateCommandDataDestinationsInner.from_dict(_item)
                    for _item in obj["dataDestinations"]
                ]
                if obj.get("dataDestinations") is not None
                else None,
                "parentId": obj.get("parentId"),
                "emailTrigger": EmailAgentTriggerCreate.from_dict(obj["emailTrigger"])
                if obj.get("emailTrigger") is not None
                else None,
                "workspaceId": obj.get("workspaceId"),
            }
        )
        # store additional fields in additional_properties
        for _key in obj.keys():
            if _key not in cls.__properties:
                _obj.additional_properties[_key] = obj.get(_key)

        return _obj
