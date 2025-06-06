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


class ScheduleStatus(str, Enum):
    """
    ScheduleStatus
    """

    """
    allowed enum values
    """
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ENDED = "ENDED"

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of ScheduleStatus from a JSON string"""
        return cls(json.loads(json_str))
