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
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr
from typing_extensions import Self

from askui.tools.askui.askui_workspaces.models.run_status import RunStatus
from askui.tools.askui.askui_workspaces.models.run_template import RunTemplate
from askui.tools.askui.askui_workspaces.models.schedule_reponse_dto import (
    ScheduleReponseDto,
)


class RunResponseDto(BaseModel):
    """
    RunResponseDto
    """  # noqa: E501

    version: Optional[StrictStr] = None
    id: Optional[StrictStr] = None
    created_at: Optional[datetime] = None
    name: StrictStr
    status: Optional[RunStatus] = None
    to_be_started_at: datetime
    started_at: Optional[datetime] = None
    schedule_id: StrictStr
    template: RunTemplate
    ended_at: Optional[datetime] = None
    no: StrictInt
    schedule: ScheduleReponseDto
    additional_properties: Dict[str, Any] = {}
    __properties: ClassVar[List[str]] = [
        "version",
        "id",
        "created_at",
        "name",
        "status",
        "to_be_started_at",
        "started_at",
        "schedule_id",
        "template",
        "ended_at",
        "no",
        "schedule",
    ]

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
        """Create an instance of RunResponseDto from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of template
        if self.template:
            _dict["template"] = self.template.to_dict()
        # override the default output from pydantic by calling `to_dict()` of schedule
        if self.schedule:
            _dict["schedule"] = self.schedule.to_dict()
        # puts key-value pairs in additional_properties in the top level
        if self.additional_properties is not None:
            for _key, _value in self.additional_properties.items():
                _dict[_key] = _value

        # set to None if started_at (nullable) is None
        # and model_fields_set contains the field
        if self.started_at is None and "started_at" in self.model_fields_set:
            _dict["started_at"] = None

        # set to None if ended_at (nullable) is None
        # and model_fields_set contains the field
        if self.ended_at is None and "ended_at" in self.model_fields_set:
            _dict["ended_at"] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of RunResponseDto from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "version": obj.get("version"),
                "id": obj.get("id"),
                "created_at": obj.get("created_at"),
                "name": obj.get("name"),
                "status": obj.get("status"),
                "to_be_started_at": obj.get("to_be_started_at"),
                "started_at": obj.get("started_at"),
                "schedule_id": obj.get("schedule_id"),
                "template": RunTemplate.from_dict(obj["template"])
                if obj.get("template") is not None
                else None,
                "ended_at": obj.get("ended_at"),
                "no": obj.get("no"),
                "schedule": ScheduleReponseDto.from_dict(obj["schedule"])
                if obj.get("schedule") is not None
                else None,
            }
        )
        # store additional fields in additional_properties
        for _key in obj.keys():
            if _key not in cls.__properties:
                _obj.additional_properties[_key] = obj.get(_key)

        return _obj
