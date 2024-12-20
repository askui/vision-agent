# coding: utf-8

"""
    AskUI Workspaces API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 0.1.24
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from askui.tools.askui.askui_workspaces.models.agent_execution_state_delivered_to_destination_deliveries_inner import AgentExecutionStateDeliveredToDestinationDeliveriesInner
from typing import Optional, Set
from typing_extensions import Self

class AgentExecutionStateDeliveredToDestination(BaseModel):
    """
    AgentExecutionStateDeliveredToDestination
    """ # noqa: E501
    status: Optional[StrictStr] = Field(default='DELIVERED_TO_DESTINATION', description="The extracted data was successfully delivered to the destination(s), e.g., an AskUI workflow invoked with the data.")
    data_extracted: Dict[str, Any] = Field(alias="dataExtracted")
    data_confirmed: Dict[str, Any] = Field(alias="dataConfirmed")
    deliveries: Optional[List[AgentExecutionStateDeliveredToDestinationDeliveriesInner]] = None
    additional_properties: Dict[str, Any] = {}
    __properties: ClassVar[List[str]] = ["status", "dataExtracted", "dataConfirmed", "deliveries"]

    @field_validator('status')
    def status_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['DELIVERED_TO_DESTINATION']):
            raise ValueError("must be one of enum values ('DELIVERED_TO_DESTINATION')")
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
        """Create an instance of AgentExecutionStateDeliveredToDestination from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of each item in deliveries (list)
        _items = []
        if self.deliveries:
            for _item in self.deliveries:
                if _item:
                    _items.append(_item.to_dict())
            _dict['deliveries'] = _items
        # puts key-value pairs in additional_properties in the top level
        if self.additional_properties is not None:
            for _key, _value in self.additional_properties.items():
                _dict[_key] = _value

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of AgentExecutionStateDeliveredToDestination from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "status": obj.get("status") if obj.get("status") is not None else 'DELIVERED_TO_DESTINATION',
            "dataExtracted": obj.get("dataExtracted"),
            "dataConfirmed": obj.get("dataConfirmed"),
            "deliveries": [AgentExecutionStateDeliveredToDestinationDeliveriesInner.from_dict(_item) for _item in obj["deliveries"]] if obj.get("deliveries") is not None else None
        })
        # store additional fields in additional_properties
        for _key in obj.keys():
            if _key not in cls.__properties:
                _obj.additional_properties[_key] = obj.get(_key)

        return _obj


