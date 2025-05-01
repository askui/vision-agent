from typing import (
    ClassVar as _ClassVar,
)
from typing import (
    Iterable as _Iterable,
)
from typing import (
    Mapping as _Mapping,
)
from typing import (
    Optional as _Optional,
)
from typing import (
    Union as _Union,
)

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

DESCRIPTOR: _descriptor.FileDescriptor

class PollEventID(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PollEventID_Undefined: _ClassVar[PollEventID]
    PollEventID_ActionFinished: _ClassVar[PollEventID]

class MouseButton(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MouseButton_Undefined: _ClassVar[MouseButton]
    MouseButton_Left: _ClassVar[MouseButton]
    MouseButton_Right: _ClassVar[MouseButton]
    MouseButton_Middle: _ClassVar[MouseButton]

class ActionClassID(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ActionClassID_Undefined: _ClassVar[ActionClassID]
    ActionClassID_Wait: _ClassVar[ActionClassID]
    ActionClassID_MouseButton_Press: _ClassVar[ActionClassID]
    ActionClassID_MouseButton_Release: _ClassVar[ActionClassID]
    ActionClassID_MouseButton_PressAndRelease: _ClassVar[ActionClassID]
    ActionClassID_MouseWheelScroll: _ClassVar[ActionClassID]
    ActionClassID_MouseMove: _ClassVar[ActionClassID]
    ActionClassID_MouseMove_Delta: _ClassVar[ActionClassID]
    ActionClassID_KeyboardKey_Press: _ClassVar[ActionClassID]
    ActionClassID_KeyboardKey_Release: _ClassVar[ActionClassID]
    ActionClassID_KeyboardKey_PressAndRelease: _ClassVar[ActionClassID]
    ActionClassID_KeyboardKeys_Press: _ClassVar[ActionClassID]
    ActionClassID_KeyboardKeys_Release: _ClassVar[ActionClassID]
    ActionClassID_KeyboardKeys_PressAndRelease: _ClassVar[ActionClassID]
    ActionClassID_KeyboardType_Text: _ClassVar[ActionClassID]
    ActionClassID_KeyboardType_UnicodeText: _ClassVar[ActionClassID]
    ActionClassID_RunCommand: _ClassVar[ActionClassID]

class MouseWheelDeltaType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MouseWheelDelta_Undefined: _ClassVar[MouseWheelDeltaType]
    MouseWheelDelta_Raw: _ClassVar[MouseWheelDeltaType]
    MouseWheelDelta_Detent: _ClassVar[MouseWheelDeltaType]

class MouseWheelScrollDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MouseWheelScrollDirection_Undefined: _ClassVar[MouseWheelScrollDirection]
    MouseWheelScrollDirection_Vertical: _ClassVar[MouseWheelScrollDirection]
    MouseWheelScrollDirection_Horizontal: _ClassVar[MouseWheelScrollDirection]

class TypingSpeedValue(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TypingSpeedValue_Undefined: _ClassVar[TypingSpeedValue]
    TypingSpeedValue_CharactersPerSecond: _ClassVar[TypingSpeedValue]
    TypingSpeedValue_Seconds: _ClassVar[TypingSpeedValue]

PollEventID_Undefined: PollEventID
PollEventID_ActionFinished: PollEventID
MouseButton_Undefined: MouseButton
MouseButton_Left: MouseButton
MouseButton_Right: MouseButton
MouseButton_Middle: MouseButton
ActionClassID_Undefined: ActionClassID
ActionClassID_Wait: ActionClassID
ActionClassID_MouseButton_Press: ActionClassID
ActionClassID_MouseButton_Release: ActionClassID
ActionClassID_MouseButton_PressAndRelease: ActionClassID
ActionClassID_MouseWheelScroll: ActionClassID
ActionClassID_MouseMove: ActionClassID
ActionClassID_MouseMove_Delta: ActionClassID
ActionClassID_KeyboardKey_Press: ActionClassID
ActionClassID_KeyboardKey_Release: ActionClassID
ActionClassID_KeyboardKey_PressAndRelease: ActionClassID
ActionClassID_KeyboardKeys_Press: ActionClassID
ActionClassID_KeyboardKeys_Release: ActionClassID
ActionClassID_KeyboardKeys_PressAndRelease: ActionClassID
ActionClassID_KeyboardType_Text: ActionClassID
ActionClassID_KeyboardType_UnicodeText: ActionClassID
ActionClassID_RunCommand: ActionClassID
MouseWheelDelta_Undefined: MouseWheelDeltaType
MouseWheelDelta_Raw: MouseWheelDeltaType
MouseWheelDelta_Detent: MouseWheelDeltaType
MouseWheelScrollDirection_Undefined: MouseWheelScrollDirection
MouseWheelScrollDirection_Vertical: MouseWheelScrollDirection
MouseWheelScrollDirection_Horizontal: MouseWheelScrollDirection
TypingSpeedValue_Undefined: TypingSpeedValue
TypingSpeedValue_CharactersPerSecond: TypingSpeedValue
TypingSpeedValue_Seconds: TypingSpeedValue

class Void(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Request_Void(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Response_Void(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Size2(_message.Message):
    __slots__ = ("width", "height")
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    width: int
    height: int
    def __init__(
        self, width: _Optional[int] = ..., height: _Optional[int] = ...
    ) -> None: ...

class Delta2(_message.Message):
    __slots__ = ("x", "y")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ...) -> None: ...

class Coordinate2(_message.Message):
    __slots__ = ("x", "y")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ...) -> None: ...

class Rectangle(_message.Message):
    __slots__ = ("left", "top", "right", "bottom")
    LEFT_FIELD_NUMBER: _ClassVar[int]
    TOP_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    BOTTOM_FIELD_NUMBER: _ClassVar[int]
    left: int
    top: int
    right: int
    bottom: int
    def __init__(
        self,
        left: _Optional[int] = ...,
        top: _Optional[int] = ...,
        right: _Optional[int] = ...,
        bottom: _Optional[int] = ...,
    ) -> None: ...

class Bitmap(_message.Message):
    __slots__ = (
        "width",
        "height",
        "lineWidth",
        "bitsPerPixel",
        "bytesPerPixel",
        "data",
    )
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    LINEWIDTH_FIELD_NUMBER: _ClassVar[int]
    BITSPERPIXEL_FIELD_NUMBER: _ClassVar[int]
    BYTESPERPIXEL_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    width: int
    height: int
    lineWidth: int
    bitsPerPixel: int
    bytesPerPixel: int
    data: bytes
    def __init__(
        self,
        width: _Optional[int] = ...,
        height: _Optional[int] = ...,
        lineWidth: _Optional[int] = ...,
        bitsPerPixel: _Optional[int] = ...,
        bytesPerPixel: _Optional[int] = ...,
        data: _Optional[bytes] = ...,
    ) -> None: ...

class Color(_message.Message):
    __slots__ = ("r", "g", "b")
    R_FIELD_NUMBER: _ClassVar[int]
    G_FIELD_NUMBER: _ClassVar[int]
    B_FIELD_NUMBER: _ClassVar[int]
    r: int
    g: int
    b: int
    def __init__(
        self, r: _Optional[int] = ..., g: _Optional[int] = ..., b: _Optional[int] = ...
    ) -> None: ...

class GUID(_message.Message):
    __slots__ = ("highPart", "lowPart")
    HIGHPART_FIELD_NUMBER: _ClassVar[int]
    LOWPART_FIELD_NUMBER: _ClassVar[int]
    highPart: int
    lowPart: int
    def __init__(
        self, highPart: _Optional[int] = ..., lowPart: _Optional[int] = ...
    ) -> None: ...

class SessionInfo(_message.Message):
    __slots__ = ("sessionGUID", "sessionID")
    SESSIONGUID_FIELD_NUMBER: _ClassVar[int]
    SESSIONID_FIELD_NUMBER: _ClassVar[int]
    sessionGUID: GUID
    sessionID: int
    def __init__(
        self,
        sessionGUID: _Optional[_Union[GUID, _Mapping]] = ...,
        sessionID: _Optional[int] = ...,
    ) -> None: ...

class CaptureArea(_message.Message):
    __slots__ = ("size", "coordinate")
    SIZE_FIELD_NUMBER: _ClassVar[int]
    COORDINATE_FIELD_NUMBER: _ClassVar[int]
    size: Size2
    coordinate: Coordinate2
    def __init__(
        self,
        size: _Optional[_Union[Size2, _Mapping]] = ...,
        coordinate: _Optional[_Union[Coordinate2, _Mapping]] = ...,
    ) -> None: ...

class CaptureParameters(_message.Message):
    __slots__ = ("displayID", "captureArea")
    DISPLAYID_FIELD_NUMBER: _ClassVar[int]
    CAPTUREAREA_FIELD_NUMBER: _ClassVar[int]
    displayID: int
    captureArea: CaptureArea
    def __init__(
        self,
        displayID: _Optional[int] = ...,
        captureArea: _Optional[_Union[CaptureArea, _Mapping]] = ...,
    ) -> None: ...

class PollEventParameters_ActionFinished(_message.Message):
    __slots__ = ("actionID",)
    ACTIONID_FIELD_NUMBER: _ClassVar[int]
    actionID: int
    def __init__(self, actionID: _Optional[int] = ...) -> None: ...

class PollEventParameters(_message.Message):
    __slots__ = ("actionFinished",)
    ACTIONFINISHED_FIELD_NUMBER: _ClassVar[int]
    actionFinished: PollEventParameters_ActionFinished
    def __init__(
        self,
        actionFinished: _Optional[
            _Union[PollEventParameters_ActionFinished, _Mapping]
        ] = ...,
    ) -> None: ...

class ActionParameters_Wait(_message.Message):
    __slots__ = ("milliseconds",)
    MILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    milliseconds: int
    def __init__(self, milliseconds: _Optional[int] = ...) -> None: ...

class ActionParameters_MouseButton_Press(_message.Message):
    __slots__ = ("mouseButton",)
    MOUSEBUTTON_FIELD_NUMBER: _ClassVar[int]
    mouseButton: MouseButton
    def __init__(
        self, mouseButton: _Optional[_Union[MouseButton, str]] = ...
    ) -> None: ...

class ActionParameters_MouseButton_Release(_message.Message):
    __slots__ = ("mouseButton",)
    MOUSEBUTTON_FIELD_NUMBER: _ClassVar[int]
    mouseButton: MouseButton
    def __init__(
        self, mouseButton: _Optional[_Union[MouseButton, str]] = ...
    ) -> None: ...

class ActionParameters_MouseButton_PressAndRelease(_message.Message):
    __slots__ = ("mouseButton", "count")
    MOUSEBUTTON_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    mouseButton: MouseButton
    count: int
    def __init__(
        self,
        mouseButton: _Optional[_Union[MouseButton, str]] = ...,
        count: _Optional[int] = ...,
    ) -> None: ...

class ActionParameters_MouseWheelScroll(_message.Message):
    __slots__ = ("direction", "deltaType", "delta", "milliseconds")
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    DELTATYPE_FIELD_NUMBER: _ClassVar[int]
    DELTA_FIELD_NUMBER: _ClassVar[int]
    MILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    direction: MouseWheelScrollDirection
    deltaType: MouseWheelDeltaType
    delta: int
    milliseconds: int
    def __init__(
        self,
        direction: _Optional[_Union[MouseWheelScrollDirection, str]] = ...,
        deltaType: _Optional[_Union[MouseWheelDeltaType, str]] = ...,
        delta: _Optional[int] = ...,
        milliseconds: _Optional[int] = ...,
    ) -> None: ...

class ActionParameters_MouseMove(_message.Message):
    __slots__ = ("position", "milliseconds")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    MILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    position: Coordinate2
    milliseconds: int
    def __init__(
        self,
        position: _Optional[_Union[Coordinate2, _Mapping]] = ...,
        milliseconds: _Optional[int] = ...,
    ) -> None: ...

class ActionParameters_MouseMove_Delta(_message.Message):
    __slots__ = ("delta", "milliseconds")
    DELTA_FIELD_NUMBER: _ClassVar[int]
    MILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    delta: Delta2
    milliseconds: int
    def __init__(
        self,
        delta: _Optional[_Union[Delta2, _Mapping]] = ...,
        milliseconds: _Optional[int] = ...,
    ) -> None: ...

class ActionParameters_KeyboardKey_Press(_message.Message):
    __slots__ = ("keyName", "modifierKeyNames")
    KEYNAME_FIELD_NUMBER: _ClassVar[int]
    MODIFIERKEYNAMES_FIELD_NUMBER: _ClassVar[int]
    keyName: str
    modifierKeyNames: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        keyName: _Optional[str] = ...,
        modifierKeyNames: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class ActionParameters_KeyboardKey_Release(_message.Message):
    __slots__ = ("keyName", "modifierKeyNames")
    KEYNAME_FIELD_NUMBER: _ClassVar[int]
    MODIFIERKEYNAMES_FIELD_NUMBER: _ClassVar[int]
    keyName: str
    modifierKeyNames: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        keyName: _Optional[str] = ...,
        modifierKeyNames: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class ActionParameters_KeyboardKey_PressAndRelease(_message.Message):
    __slots__ = ("keyName", "modifierKeyNames")
    KEYNAME_FIELD_NUMBER: _ClassVar[int]
    MODIFIERKEYNAMES_FIELD_NUMBER: _ClassVar[int]
    keyName: str
    modifierKeyNames: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        keyName: _Optional[str] = ...,
        modifierKeyNames: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class ActionParameters_KeyboardKeys_Press(_message.Message):
    __slots__ = ("keyNames", "modifierKeyNames")
    KEYNAMES_FIELD_NUMBER: _ClassVar[int]
    MODIFIERKEYNAMES_FIELD_NUMBER: _ClassVar[int]
    keyNames: _containers.RepeatedScalarFieldContainer[str]
    modifierKeyNames: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        keyNames: _Optional[_Iterable[str]] = ...,
        modifierKeyNames: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class ActionParameters_KeyboardKeys_Release(_message.Message):
    __slots__ = ("keyNames", "modifierKeyNames")
    KEYNAMES_FIELD_NUMBER: _ClassVar[int]
    MODIFIERKEYNAMES_FIELD_NUMBER: _ClassVar[int]
    keyNames: _containers.RepeatedScalarFieldContainer[str]
    modifierKeyNames: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        keyNames: _Optional[_Iterable[str]] = ...,
        modifierKeyNames: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class ActionParameters_KeyboardKeys_PressAndRelease(_message.Message):
    __slots__ = ("keyNames", "modifierKeyNames")
    KEYNAMES_FIELD_NUMBER: _ClassVar[int]
    MODIFIERKEYNAMES_FIELD_NUMBER: _ClassVar[int]
    keyNames: _containers.RepeatedScalarFieldContainer[str]
    modifierKeyNames: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        keyNames: _Optional[_Iterable[str]] = ...,
        modifierKeyNames: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class ActionParameters_KeyboardType_Text(_message.Message):
    __slots__ = ("text", "typingSpeedValue", "typingSpeed")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TYPINGSPEEDVALUE_FIELD_NUMBER: _ClassVar[int]
    TYPINGSPEED_FIELD_NUMBER: _ClassVar[int]
    text: str
    typingSpeedValue: TypingSpeedValue
    typingSpeed: int
    def __init__(
        self,
        text: _Optional[str] = ...,
        typingSpeedValue: _Optional[_Union[TypingSpeedValue, str]] = ...,
        typingSpeed: _Optional[int] = ...,
    ) -> None: ...

class ActionParameters_KeyboardType_UnicodeText(_message.Message):
    __slots__ = ("text", "typingSpeedValue", "typingSpeed")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TYPINGSPEEDVALUE_FIELD_NUMBER: _ClassVar[int]
    TYPINGSPEED_FIELD_NUMBER: _ClassVar[int]
    text: bytes
    typingSpeedValue: TypingSpeedValue
    typingSpeed: int
    def __init__(
        self,
        text: _Optional[bytes] = ...,
        typingSpeedValue: _Optional[_Union[TypingSpeedValue, str]] = ...,
        typingSpeed: _Optional[int] = ...,
    ) -> None: ...

class ActionParameters_RunCommand(_message.Message):
    __slots__ = ("command", "timeoutInMilliseconds")
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    TIMEOUTINMILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    command: str
    timeoutInMilliseconds: int
    def __init__(
        self, command: _Optional[str] = ..., timeoutInMilliseconds: _Optional[int] = ...
    ) -> None: ...

class ActionParameters(_message.Message):
    __slots__ = (
        "none",
        "wait",
        "mouseButtonPress",
        "mouseButtonRelease",
        "mouseButtonPressAndRelease",
        "mouseWheelScroll",
        "mouseMove",
        "mouseMoveDelta",
        "keyboardKeyPress",
        "keyboardKeyRelease",
        "keyboardKeyPressAndRelease",
        "keyboardKeysPress",
        "keyboardKeysRelease",
        "keyboardKeysPressAndRelease",
        "keyboardTypeText",
        "keyboardTypeUnicodeText",
        "runcommand",
    )
    NONE_FIELD_NUMBER: _ClassVar[int]
    WAIT_FIELD_NUMBER: _ClassVar[int]
    MOUSEBUTTONPRESS_FIELD_NUMBER: _ClassVar[int]
    MOUSEBUTTONRELEASE_FIELD_NUMBER: _ClassVar[int]
    MOUSEBUTTONPRESSANDRELEASE_FIELD_NUMBER: _ClassVar[int]
    MOUSEWHEELSCROLL_FIELD_NUMBER: _ClassVar[int]
    MOUSEMOVE_FIELD_NUMBER: _ClassVar[int]
    MOUSEMOVEDELTA_FIELD_NUMBER: _ClassVar[int]
    KEYBOARDKEYPRESS_FIELD_NUMBER: _ClassVar[int]
    KEYBOARDKEYRELEASE_FIELD_NUMBER: _ClassVar[int]
    KEYBOARDKEYPRESSANDRELEASE_FIELD_NUMBER: _ClassVar[int]
    KEYBOARDKEYSPRESS_FIELD_NUMBER: _ClassVar[int]
    KEYBOARDKEYSRELEASE_FIELD_NUMBER: _ClassVar[int]
    KEYBOARDKEYSPRESSANDRELEASE_FIELD_NUMBER: _ClassVar[int]
    KEYBOARDTYPETEXT_FIELD_NUMBER: _ClassVar[int]
    KEYBOARDTYPEUNICODETEXT_FIELD_NUMBER: _ClassVar[int]
    RUNCOMMAND_FIELD_NUMBER: _ClassVar[int]
    none: Void
    wait: ActionParameters_Wait
    mouseButtonPress: ActionParameters_MouseButton_Press
    mouseButtonRelease: ActionParameters_MouseButton_Release
    mouseButtonPressAndRelease: ActionParameters_MouseButton_PressAndRelease
    mouseWheelScroll: ActionParameters_MouseWheelScroll
    mouseMove: ActionParameters_MouseMove
    mouseMoveDelta: ActionParameters_MouseMove_Delta
    keyboardKeyPress: ActionParameters_KeyboardKey_Press
    keyboardKeyRelease: ActionParameters_KeyboardKey_Release
    keyboardKeyPressAndRelease: ActionParameters_KeyboardKey_PressAndRelease
    keyboardKeysPress: ActionParameters_KeyboardKeys_Press
    keyboardKeysRelease: ActionParameters_KeyboardKeys_Release
    keyboardKeysPressAndRelease: ActionParameters_KeyboardKeys_PressAndRelease
    keyboardTypeText: ActionParameters_KeyboardType_Text
    keyboardTypeUnicodeText: ActionParameters_KeyboardType_UnicodeText
    runcommand: ActionParameters_RunCommand
    def __init__(
        self,
        none: _Optional[_Union[Void, _Mapping]] = ...,
        wait: _Optional[_Union[ActionParameters_Wait, _Mapping]] = ...,
        mouseButtonPress: _Optional[
            _Union[ActionParameters_MouseButton_Press, _Mapping]
        ] = ...,
        mouseButtonRelease: _Optional[
            _Union[ActionParameters_MouseButton_Release, _Mapping]
        ] = ...,
        mouseButtonPressAndRelease: _Optional[
            _Union[ActionParameters_MouseButton_PressAndRelease, _Mapping]
        ] = ...,
        mouseWheelScroll: _Optional[
            _Union[ActionParameters_MouseWheelScroll, _Mapping]
        ] = ...,
        mouseMove: _Optional[_Union[ActionParameters_MouseMove, _Mapping]] = ...,
        mouseMoveDelta: _Optional[
            _Union[ActionParameters_MouseMove_Delta, _Mapping]
        ] = ...,
        keyboardKeyPress: _Optional[
            _Union[ActionParameters_KeyboardKey_Press, _Mapping]
        ] = ...,
        keyboardKeyRelease: _Optional[
            _Union[ActionParameters_KeyboardKey_Release, _Mapping]
        ] = ...,
        keyboardKeyPressAndRelease: _Optional[
            _Union[ActionParameters_KeyboardKey_PressAndRelease, _Mapping]
        ] = ...,
        keyboardKeysPress: _Optional[
            _Union[ActionParameters_KeyboardKeys_Press, _Mapping]
        ] = ...,
        keyboardKeysRelease: _Optional[
            _Union[ActionParameters_KeyboardKeys_Release, _Mapping]
        ] = ...,
        keyboardKeysPressAndRelease: _Optional[
            _Union[ActionParameters_KeyboardKeys_PressAndRelease, _Mapping]
        ] = ...,
        keyboardTypeText: _Optional[
            _Union[ActionParameters_KeyboardType_Text, _Mapping]
        ] = ...,
        keyboardTypeUnicodeText: _Optional[
            _Union[ActionParameters_KeyboardType_UnicodeText, _Mapping]
        ] = ...,
        runcommand: _Optional[_Union[ActionParameters_RunCommand, _Mapping]] = ...,
    ) -> None: ...

class Request_StartSession(_message.Message):
    __slots__ = ("sessionGUID", "immediateExecution")
    SESSIONGUID_FIELD_NUMBER: _ClassVar[int]
    IMMEDIATEEXECUTION_FIELD_NUMBER: _ClassVar[int]
    sessionGUID: str
    immediateExecution: bool
    def __init__(
        self, sessionGUID: _Optional[str] = ..., immediateExecution: bool = ...
    ) -> None: ...

class Response_StartSession(_message.Message):
    __slots__ = ("sessionInfo",)
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    def __init__(
        self, sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...
    ) -> None: ...

class Request_EndSession(_message.Message):
    __slots__ = ("sessionInfo",)
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    def __init__(
        self, sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...
    ) -> None: ...

class Request_Poll(_message.Message):
    __slots__ = ("sessionInfo", "pollEventID")
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    POLLEVENTID_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    pollEventID: PollEventID
    def __init__(
        self,
        sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...,
        pollEventID: _Optional[_Union[PollEventID, str]] = ...,
    ) -> None: ...

class Request_StartExecution(_message.Message):
    __slots__ = ("sessionInfo",)
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    def __init__(
        self, sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...
    ) -> None: ...

class Request_StopExecution(_message.Message):
    __slots__ = ("sessionInfo",)
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    def __init__(
        self, sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...
    ) -> None: ...

class Response_Poll(_message.Message):
    __slots__ = ("pollEventID", "pollEventParameters")
    POLLEVENTID_FIELD_NUMBER: _ClassVar[int]
    POLLEVENTPARAMETERS_FIELD_NUMBER: _ClassVar[int]
    pollEventID: PollEventID
    pollEventParameters: PollEventParameters
    def __init__(
        self,
        pollEventID: _Optional[_Union[PollEventID, str]] = ...,
        pollEventParameters: _Optional[_Union[PollEventParameters, _Mapping]] = ...,
    ) -> None: ...

class Request_RunRecordedAction(_message.Message):
    __slots__ = ("sessionInfo", "actionClassID", "actionParameters")
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    ACTIONCLASSID_FIELD_NUMBER: _ClassVar[int]
    ACTIONPARAMETERS_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    actionClassID: ActionClassID
    actionParameters: ActionParameters
    def __init__(
        self,
        sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...,
        actionClassID: _Optional[_Union[ActionClassID, str]] = ...,
        actionParameters: _Optional[_Union[ActionParameters, _Mapping]] = ...,
    ) -> None: ...

class Response_RunRecordedAction(_message.Message):
    __slots__ = ("actionID", "requiredMilliseconds")
    ACTIONID_FIELD_NUMBER: _ClassVar[int]
    REQUIREDMILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    actionID: int
    requiredMilliseconds: int
    def __init__(
        self, actionID: _Optional[int] = ..., requiredMilliseconds: _Optional[int] = ...
    ) -> None: ...

class Request_ScheduleBatchedAction(_message.Message):
    __slots__ = ("sessionInfo", "actionClassID", "actionParameters")
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    ACTIONCLASSID_FIELD_NUMBER: _ClassVar[int]
    ACTIONPARAMETERS_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    actionClassID: ActionClassID
    actionParameters: ActionParameters
    def __init__(
        self,
        sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...,
        actionClassID: _Optional[_Union[ActionClassID, str]] = ...,
        actionParameters: _Optional[_Union[ActionParameters, _Mapping]] = ...,
    ) -> None: ...

class Response_ScheduleBatchedAction(_message.Message):
    __slots__ = ("actionID",)
    ACTIONID_FIELD_NUMBER: _ClassVar[int]
    actionID: int
    def __init__(self, actionID: _Optional[int] = ...) -> None: ...

class Request_GetActionCount(_message.Message):
    __slots__ = ("sessionInfo",)
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    def __init__(
        self, sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...
    ) -> None: ...

class Response_GetActionCount(_message.Message):
    __slots__ = ("actionCount",)
    ACTIONCOUNT_FIELD_NUMBER: _ClassVar[int]
    actionCount: int
    def __init__(self, actionCount: _Optional[int] = ...) -> None: ...

class Request_GetAction(_message.Message):
    __slots__ = ("sessionInfo", "actionIndex")
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    ACTIONINDEX_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    actionIndex: int
    def __init__(
        self,
        sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...,
        actionIndex: _Optional[int] = ...,
    ) -> None: ...

class Response_GetAction(_message.Message):
    __slots__ = ("actionID", "actionClassID", "actionParameters")
    ACTIONID_FIELD_NUMBER: _ClassVar[int]
    ACTIONCLASSID_FIELD_NUMBER: _ClassVar[int]
    ACTIONPARAMETERS_FIELD_NUMBER: _ClassVar[int]
    actionID: int
    actionClassID: ActionClassID
    actionParameters: ActionParameters
    def __init__(
        self,
        actionID: _Optional[int] = ...,
        actionClassID: _Optional[_Union[ActionClassID, str]] = ...,
        actionParameters: _Optional[_Union[ActionParameters, _Mapping]] = ...,
    ) -> None: ...

class Request_RemoveAction(_message.Message):
    __slots__ = ("sessionInfo", "actionID")
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    ACTIONID_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    actionID: int
    def __init__(
        self,
        sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...,
        actionID: _Optional[int] = ...,
    ) -> None: ...

class Request_RemoveAllActions(_message.Message):
    __slots__ = ("sessionInfo",)
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    def __init__(
        self, sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...
    ) -> None: ...

class Request_StartBatchRun(_message.Message):
    __slots__ = ("sessionInfo",)
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    def __init__(
        self, sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...
    ) -> None: ...

class Request_StopBatchRun(_message.Message):
    __slots__ = ("sessionInfo",)
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    def __init__(
        self, sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...
    ) -> None: ...

class Request_CaptureScreen(_message.Message):
    __slots__ = ("sessionInfo", "captureParameters")
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    CAPTUREPARAMETERS_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    captureParameters: CaptureParameters
    def __init__(
        self,
        sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...,
        captureParameters: _Optional[_Union[CaptureParameters, _Mapping]] = ...,
    ) -> None: ...

class Response_CaptureScreen(_message.Message):
    __slots__ = ("bitmap",)
    BITMAP_FIELD_NUMBER: _ClassVar[int]
    bitmap: Bitmap
    def __init__(self, bitmap: _Optional[_Union[Bitmap, _Mapping]] = ...) -> None: ...

class Response_GetContinuousCapturedScreen(_message.Message):
    __slots__ = ("bitmap",)
    BITMAP_FIELD_NUMBER: _ClassVar[int]
    bitmap: Bitmap
    def __init__(self, bitmap: _Optional[_Union[Bitmap, _Mapping]] = ...) -> None: ...

class Reuqest_SetTestConfiguration(_message.Message):
    __slots__ = (
        "sessionInfo",
        "defaultCaptureParameters",
        "mouseDelayInMilliseconds",
        "keyboardDelayInMilliseconds",
    )
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    DEFAULTCAPTUREPARAMETERS_FIELD_NUMBER: _ClassVar[int]
    MOUSEDELAYINMILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    KEYBOARDDELAYINMILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    defaultCaptureParameters: CaptureParameters
    mouseDelayInMilliseconds: int
    keyboardDelayInMilliseconds: int
    def __init__(
        self,
        sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...,
        defaultCaptureParameters: _Optional[_Union[CaptureParameters, _Mapping]] = ...,
        mouseDelayInMilliseconds: _Optional[int] = ...,
        keyboardDelayInMilliseconds: _Optional[int] = ...,
    ) -> None: ...

class Request_SetMouseDelay(_message.Message):
    __slots__ = ("sessionInfo", "delayInMilliseconds")
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    DELAYINMILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    delayInMilliseconds: int
    def __init__(
        self,
        sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...,
        delayInMilliseconds: _Optional[int] = ...,
    ) -> None: ...

class Request_SetKeyboardDelay(_message.Message):
    __slots__ = ("sessionInfo", "delayInMilliseconds")
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    DELAYINMILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    delayInMilliseconds: int
    def __init__(
        self,
        sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...,
        delayInMilliseconds: _Optional[int] = ...,
    ) -> None: ...

class DisplayInformation(_message.Message):
    __slots__ = ("displayID", "name", "sizeInPixels", "virtualScreenRectangle")
    DISPLAYID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIZEINPIXELS_FIELD_NUMBER: _ClassVar[int]
    VIRTUALSCREENRECTANGLE_FIELD_NUMBER: _ClassVar[int]
    displayID: int
    name: str
    sizeInPixels: Size2
    virtualScreenRectangle: Rectangle
    def __init__(
        self,
        displayID: _Optional[int] = ...,
        name: _Optional[str] = ...,
        sizeInPixels: _Optional[_Union[Size2, _Mapping]] = ...,
        virtualScreenRectangle: _Optional[_Union[Rectangle, _Mapping]] = ...,
    ) -> None: ...

class Response_GetDisplayInformation(_message.Message):
    __slots__ = ("displays", "virtualScreenRectangle")
    DISPLAYS_FIELD_NUMBER: _ClassVar[int]
    VIRTUALSCREENRECTANGLE_FIELD_NUMBER: _ClassVar[int]
    displays: _containers.RepeatedCompositeFieldContainer[DisplayInformation]
    virtualScreenRectangle: Rectangle
    def __init__(
        self,
        displays: _Optional[_Iterable[_Union[DisplayInformation, _Mapping]]] = ...,
        virtualScreenRectangle: _Optional[_Union[Rectangle, _Mapping]] = ...,
    ) -> None: ...

class Response_GetMousePosition(_message.Message):
    __slots__ = ("x", "y")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ...) -> None: ...

class Request_SetActiveDisplay(_message.Message):
    __slots__ = ("displayID",)
    DISPLAYID_FIELD_NUMBER: _ClassVar[int]
    displayID: int
    def __init__(self, displayID: _Optional[int] = ...) -> None: ...

class Request_GetColor(_message.Message):
    __slots__ = ("x", "y", "bitmap")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    BITMAP_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    bitmap: Bitmap
    def __init__(
        self,
        x: _Optional[int] = ...,
        y: _Optional[int] = ...,
        bitmap: _Optional[_Union[Bitmap, _Mapping]] = ...,
    ) -> None: ...

class Response_GetColor(_message.Message):
    __slots__ = ("color",)
    COLOR_FIELD_NUMBER: _ClassVar[int]
    color: Color
    def __init__(self, color: _Optional[_Union[Color, _Mapping]] = ...) -> None: ...

class Request_GetPixelColor(_message.Message):
    __slots__ = ("x", "y")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ...) -> None: ...

class Response_GetPixelColor(_message.Message):
    __slots__ = ("color",)
    COLOR_FIELD_NUMBER: _ClassVar[int]
    color: Color
    def __init__(self, color: _Optional[_Union[Color, _Mapping]] = ...) -> None: ...

class Request_SetDisplayLabel(_message.Message):
    __slots__ = ("sessionInfo", "displayID", "label")
    SESSIONINFO_FIELD_NUMBER: _ClassVar[int]
    DISPLAYID_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    sessionInfo: SessionInfo
    displayID: int
    label: str
    def __init__(
        self,
        sessionInfo: _Optional[_Union[SessionInfo, _Mapping]] = ...,
        displayID: _Optional[int] = ...,
        label: _Optional[str] = ...,
    ) -> None: ...
