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


class RunStatus(str, Enum):
    """
    RunStatus
    """

    """
    allowed enum values
    """
    UPCOMING = "UPCOMING"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SKIPPED = "SKIPPED"
    SKIPPED_NOTHING_TO_RUN = "SKIPPED_NOTHING_TO_RUN"
    PASSED_NOT_YET_REPORTED = "PASSED_NOT_YET_REPORTED"
    FAILED_NOT_YET_REPORTED = "FAILED_NOT_YET_REPORTED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    SUSPENDED = "SUSPENDED"

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of RunStatus from a JSON string"""
        return cls(json.loads(json_str))
