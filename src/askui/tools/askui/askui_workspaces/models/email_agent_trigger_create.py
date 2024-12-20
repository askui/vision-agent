# coding: utf-8

"""
    AskUI Workspaces API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 0.1.30
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Annotated
from typing import Optional, Set
from typing_extensions import Self

class EmailAgentTriggerCreate(BaseModel):
    """
    EmailAgentTriggerCreate
    """ # noqa: E501
    active: Optional[StrictBool] = Field(default=True, description="If false, no emails can be send to trigger agent.")
    allowed_senders: Optional[List[StrictStr]] = Field(default=None, description="The email addresses that are allowed to send emails to trigger the agent. If empty, no emails can be send to trigger agent.", alias="allowedSenders")
    local_part: Optional[Annotated[str, Field(strict=True)]] = Field(default=None, alias="localPart")
    additional_properties: Dict[str, Any] = {}
    __properties: ClassVar[List[str]] = ["active", "allowedSenders", "localPart"]

    @field_validator('local_part')
    def local_part_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if value is None:
            return value

        if not re.match(r"^[a-zA-Z0-9-_.+]+$", value):
            raise ValueError(r"must validate the regular expression /^[a-zA-Z0-9-_.+]+$/")
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
        """Create an instance of EmailAgentTriggerCreate from a JSON string"""
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
        excluded_fields: Set[str] = set([
            "additional_properties",
        ])

        _dict = self.model_dump(
            by_alias=True,
            exclude=excluded_fields,
            exclude_none=True,
        )
        # puts key-value pairs in additional_properties in the top level
        if self.additional_properties is not None:
            for _key, _value in self.additional_properties.items():
                _dict[_key] = _value

        # set to None if local_part (nullable) is None
        # and model_fields_set contains the field
        if self.local_part is None and "local_part" in self.model_fields_set:
            _dict['localPart'] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of EmailAgentTriggerCreate from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "active": obj.get("active") if obj.get("active") is not None else True,
            "allowedSenders": obj.get("allowedSenders"),
            "localPart": obj.get("localPart")
        })
        # store additional fields in additional_properties
        for _key in obj.keys():
            if _key not in cls.__properties:
                _obj.additional_properties[_key] = obj.get(_key)

        return _obj


