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
from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError, field_validator
from typing import Any, List, Optional
from askui.tools.askui.askui_workspaces.models.agent_execution_cancel import AgentExecutionCancel
from askui.tools.askui.askui_workspaces.models.agent_execution_confirm import AgentExecutionConfirm
from askui.tools.askui.askui_workspaces.models.agent_execution_pending_review import AgentExecutionPendingReview
from askui.tools.askui.askui_workspaces.models.agent_execution_state_delivered_to_destination_input import AgentExecutionStateDeliveredToDestinationInput
from pydantic import StrictStr, Field
from typing import Union, List, Set, Optional, Dict
from typing_extensions import Literal, Self

STATE1_ONE_OF_SCHEMAS = ["AgentExecutionCancel", "AgentExecutionConfirm", "AgentExecutionPendingReview", "AgentExecutionStateDeliveredToDestinationInput"]

class State1(BaseModel):
    """
    State1
    """
    # data type: AgentExecutionPendingReview
    oneof_schema_1_validator: Optional[AgentExecutionPendingReview] = None
    # data type: AgentExecutionCancel
    oneof_schema_2_validator: Optional[AgentExecutionCancel] = None
    # data type: AgentExecutionConfirm
    oneof_schema_3_validator: Optional[AgentExecutionConfirm] = None
    # data type: AgentExecutionStateDeliveredToDestinationInput
    oneof_schema_4_validator: Optional[AgentExecutionStateDeliveredToDestinationInput] = None
    actual_instance: Optional[Union[AgentExecutionCancel, AgentExecutionConfirm, AgentExecutionPendingReview, AgentExecutionStateDeliveredToDestinationInput]] = None
    one_of_schemas: Set[str] = { "AgentExecutionCancel", "AgentExecutionConfirm", "AgentExecutionPendingReview", "AgentExecutionStateDeliveredToDestinationInput" }

    model_config = ConfigDict(
        validate_assignment=True,
        protected_namespaces=(),
    )


    discriminator_value_class_map: Dict[str, str] = {
    }

    def __init__(self, *args, **kwargs) -> None:
        if args:
            if len(args) > 1:
                raise ValueError("If a position argument is used, only 1 is allowed to set `actual_instance`")
            if kwargs:
                raise ValueError("If a position argument is used, keyword arguments cannot be used.")
            super().__init__(actual_instance=args[0])
        else:
            super().__init__(**kwargs)

    @field_validator('actual_instance')
    def actual_instance_must_validate_oneof(cls, v):
        instance = State1.model_construct()
        error_messages = []
        match = 0
        # validate data type: AgentExecutionPendingReview
        if not isinstance(v, AgentExecutionPendingReview):
            error_messages.append(f"Error! Input type `{type(v)}` is not `AgentExecutionPendingReview`")
        else:
            match += 1
        # validate data type: AgentExecutionCancel
        if not isinstance(v, AgentExecutionCancel):
            error_messages.append(f"Error! Input type `{type(v)}` is not `AgentExecutionCancel`")
        else:
            match += 1
        # validate data type: AgentExecutionConfirm
        if not isinstance(v, AgentExecutionConfirm):
            error_messages.append(f"Error! Input type `{type(v)}` is not `AgentExecutionConfirm`")
        else:
            match += 1
        # validate data type: AgentExecutionStateDeliveredToDestinationInput
        if not isinstance(v, AgentExecutionStateDeliveredToDestinationInput):
            error_messages.append(f"Error! Input type `{type(v)}` is not `AgentExecutionStateDeliveredToDestinationInput`")
        else:
            match += 1
        if match > 1:
            # more than 1 match
            raise ValueError("Multiple matches found when setting `actual_instance` in State1 with oneOf schemas: AgentExecutionCancel, AgentExecutionConfirm, AgentExecutionPendingReview, AgentExecutionStateDeliveredToDestinationInput. Details: " + ", ".join(error_messages))
        elif match == 0:
            # no match
            raise ValueError("No match found when setting `actual_instance` in State1 with oneOf schemas: AgentExecutionCancel, AgentExecutionConfirm, AgentExecutionPendingReview, AgentExecutionStateDeliveredToDestinationInput. Details: " + ", ".join(error_messages))
        else:
            return v

    @classmethod
    def from_dict(cls, obj: Union[str, Dict[str, Any]]) -> Self:
        return cls.from_json(json.dumps(obj))

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Returns the object represented by the json string"""
        instance = cls.model_construct()
        error_messages = []
        match = 0

        # use oneOf discriminator to lookup the data type
        _data_type = json.loads(json_str).get("status")
        if not _data_type:
            raise ValueError("Failed to lookup data type from the field `status` in the input.")

        # check if data type is `AgentExecutionCancel`
        if _data_type == "CANCELED":
            instance.actual_instance = AgentExecutionCancel.from_json(json_str)
            return instance

        # check if data type is `AgentExecutionConfirm`
        if _data_type == "CONFIRMED":
            instance.actual_instance = AgentExecutionConfirm.from_json(json_str)
            return instance

        # check if data type is `AgentExecutionStateDeliveredToDestinationInput`
        if _data_type == "DELIVERED_TO_DESTINATION":
            instance.actual_instance = AgentExecutionStateDeliveredToDestinationInput.from_json(json_str)
            return instance

        # check if data type is `AgentExecutionPendingReview`
        if _data_type == "PENDING_REVIEW":
            instance.actual_instance = AgentExecutionPendingReview.from_json(json_str)
            return instance

        # check if data type is `AgentExecutionCancel`
        if _data_type == "AgentExecutionCancel":
            instance.actual_instance = AgentExecutionCancel.from_json(json_str)
            return instance

        # check if data type is `AgentExecutionConfirm`
        if _data_type == "AgentExecutionConfirm":
            instance.actual_instance = AgentExecutionConfirm.from_json(json_str)
            return instance

        # check if data type is `AgentExecutionPendingReview`
        if _data_type == "AgentExecutionPendingReview":
            instance.actual_instance = AgentExecutionPendingReview.from_json(json_str)
            return instance

        # check if data type is `AgentExecutionStateDeliveredToDestinationInput`
        if _data_type == "AgentExecutionStateDeliveredToDestination-Input":
            instance.actual_instance = AgentExecutionStateDeliveredToDestinationInput.from_json(json_str)
            return instance

        # deserialize data into AgentExecutionPendingReview
        try:
            instance.actual_instance = AgentExecutionPendingReview.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))
        # deserialize data into AgentExecutionCancel
        try:
            instance.actual_instance = AgentExecutionCancel.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))
        # deserialize data into AgentExecutionConfirm
        try:
            instance.actual_instance = AgentExecutionConfirm.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))
        # deserialize data into AgentExecutionStateDeliveredToDestinationInput
        try:
            instance.actual_instance = AgentExecutionStateDeliveredToDestinationInput.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))

        if match > 1:
            # more than 1 match
            raise ValueError("Multiple matches found when deserializing the JSON string into State1 with oneOf schemas: AgentExecutionCancel, AgentExecutionConfirm, AgentExecutionPendingReview, AgentExecutionStateDeliveredToDestinationInput. Details: " + ", ".join(error_messages))
        elif match == 0:
            # no match
            raise ValueError("No match found when deserializing the JSON string into State1 with oneOf schemas: AgentExecutionCancel, AgentExecutionConfirm, AgentExecutionPendingReview, AgentExecutionStateDeliveredToDestinationInput. Details: " + ", ".join(error_messages))
        else:
            return instance

    def to_json(self) -> str:
        """Returns the JSON representation of the actual instance"""
        if self.actual_instance is None:
            return "null"

        if hasattr(self.actual_instance, "to_json") and callable(self.actual_instance.to_json):
            return self.actual_instance.to_json()
        else:
            return json.dumps(self.actual_instance)

    def to_dict(self) -> Optional[Union[Dict[str, Any], AgentExecutionCancel, AgentExecutionConfirm, AgentExecutionPendingReview, AgentExecutionStateDeliveredToDestinationInput]]:
        """Returns the dict representation of the actual instance"""
        if self.actual_instance is None:
            return None

        if hasattr(self.actual_instance, "to_dict") and callable(self.actual_instance.to_dict):
            return self.actual_instance.to_dict()
        else:
            # primitive type
            return self.actual_instance

    def to_str(self) -> str:
        """Returns the string representation of the actual instance"""
        return pprint.pformat(self.model_dump())


