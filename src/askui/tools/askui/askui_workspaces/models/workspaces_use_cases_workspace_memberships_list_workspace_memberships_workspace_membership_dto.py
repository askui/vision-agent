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

from pydantic import BaseModel, ConfigDict, Field, StrictStr
from typing_extensions import Self

from askui.tools.askui.askui_workspaces.models.user_dto import UserDto
from askui.tools.askui.askui_workspaces.models.workspace_dto import WorkspaceDto
from askui.tools.askui.askui_workspaces.models.workspace_privilege import (
    WorkspacePrivilege,
)


class WorkspacesUseCasesWorkspaceMembershipsListWorkspaceMembershipsWorkspaceMembershipDto(
    BaseModel
):
    """
    WorkspacesUseCasesWorkspaceMembershipsListWorkspaceMembershipsWorkspaceMembershipDto
    """  # noqa: E501

    id: Optional[StrictStr] = None
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
    privileges: List[WorkspacePrivilege]
    user: Optional[UserDto] = None
    user_id: StrictStr = Field(alias="userId")
    workspace: Optional[WorkspaceDto] = None
    workspace_id: StrictStr = Field(alias="workspaceId")
    additional_properties: Dict[str, Any] = {}
    __properties: ClassVar[List[str]] = [
        "id",
        "createdAt",
        "updatedAt",
        "privileges",
        "user",
        "userId",
        "workspace",
        "workspaceId",
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
        """Create an instance of WorkspacesUseCasesWorkspaceMembershipsListWorkspaceMembershipsWorkspaceMembershipDto from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of user
        if self.user:
            _dict["user"] = self.user.to_dict()
        # override the default output from pydantic by calling `to_dict()` of workspace
        if self.workspace:
            _dict["workspace"] = self.workspace.to_dict()
        # puts key-value pairs in additional_properties in the top level
        if self.additional_properties is not None:
            for _key, _value in self.additional_properties.items():
                _dict[_key] = _value

        # set to None if user (nullable) is None
        # and model_fields_set contains the field
        if self.user is None and "user" in self.model_fields_set:
            _dict["user"] = None

        # set to None if workspace (nullable) is None
        # and model_fields_set contains the field
        if self.workspace is None and "workspace" in self.model_fields_set:
            _dict["workspace"] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of WorkspacesUseCasesWorkspaceMembershipsListWorkspaceMembershipsWorkspaceMembershipDto from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "id": obj.get("id"),
                "createdAt": obj.get("createdAt"),
                "updatedAt": obj.get("updatedAt"),
                "privileges": obj.get("privileges"),
                "user": UserDto.from_dict(obj["user"])
                if obj.get("user") is not None
                else None,
                "userId": obj.get("userId"),
                "workspace": WorkspaceDto.from_dict(obj["workspace"])
                if obj.get("workspace") is not None
                else None,
                "workspaceId": obj.get("workspaceId"),
            }
        )
        # store additional fields in additional_properties
        for _key in obj.keys():
            if _key not in cls.__properties:
                _obj.additional_properties[_key] = obj.get(_key)

        return _obj
