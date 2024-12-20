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
from enum import Enum
from typing_extensions import Self


class WorkspacePrivilege(str, Enum):
    """
    WorkspacePrivilege
    """

    """
    allowed enum values
    """
    ROLE_WORKSPACE_OWNER = 'ROLE_WORKSPACE_OWNER'
    ROLE_WORKSPACE_ADMIN = 'ROLE_WORKSPACE_ADMIN'
    ROLE_WORKSPACE_MEMBER = 'ROLE_WORKSPACE_MEMBER'

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of WorkspacePrivilege from a JSON string"""
        return cls(json.loads(json_str))


