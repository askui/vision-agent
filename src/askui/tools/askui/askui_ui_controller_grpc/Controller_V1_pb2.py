# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: Controller_V1.proto
# Protobuf Python Version: 5.28.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x13\x43ontroller_V1.proto\x12\x0f\x41skui.API.TDKv1"\x06\n\x04Void"\x0e\n\x0cRequest_Void"\x0f\n\rResponse_Void"&\n\x05Size2\x12\r\n\x05width\x18\x01 \x01(\r\x12\x0e\n\x06height\x18\x02 \x01(\r"\x1e\n\x06\x44\x65lta2\x12\t\n\x01x\x18\x01 \x01(\x05\x12\t\n\x01y\x18\x02 \x01(\x05"#\n\x0b\x43oordinate2\x12\t\n\x01x\x18\x01 \x01(\x05\x12\t\n\x01y\x18\x02 \x01(\x05"E\n\tRectangle\x12\x0c\n\x04left\x18\x01 \x01(\x05\x12\x0b\n\x03top\x18\x02 \x01(\x05\x12\r\n\x05right\x18\x03 \x01(\x05\x12\x0e\n\x06\x62ottom\x18\x04 \x01(\x05"u\n\x06\x42itmap\x12\r\n\x05width\x18\x01 \x01(\r\x12\x0e\n\x06height\x18\x02 \x01(\r\x12\x11\n\tlineWidth\x18\x03 \x01(\r\x12\x14\n\x0c\x62itsPerPixel\x18\x04 \x01(\r\x12\x15\n\rbytesPerPixel\x18\x05 \x01(\r\x12\x0c\n\x04\x64\x61ta\x18\x06 \x01(\x0c"(\n\x05\x43olor\x12\t\n\x01r\x18\x01 \x01(\r\x12\t\n\x01g\x18\x02 \x01(\r\x12\t\n\x01\x62\x18\x03 \x01(\r")\n\x04GUID\x12\x10\n\x08highPart\x18\x01 \x01(\x04\x12\x0f\n\x07lowPart\x18\x02 \x01(\x04"L\n\x0bSessionInfo\x12*\n\x0bsessionGUID\x18\x01 \x01(\x0b\x32\x15.Askui.API.TDKv1.GUID\x12\x11\n\tsessionID\x18\x02 \x01(\x04"e\n\x0b\x43\x61ptureArea\x12$\n\x04size\x18\x03 \x01(\x0b\x32\x16.Askui.API.TDKv1.Size2\x12\x30\n\ncoordinate\x18\x02 \x01(\x0b\x32\x1c.Askui.API.TDKv1.Coordinate2"\x81\x01\n\x11\x43\x61ptureParameters\x12\x16\n\tdisplayID\x18\x01 \x01(\rH\x00\x88\x01\x01\x12\x36\n\x0b\x63\x61ptureArea\x18\x02 \x01(\x0b\x32\x1c.Askui.API.TDKv1.CaptureAreaH\x01\x88\x01\x01\x42\x0c\n\n_displayIDB\x0e\n\x0c_captureArea"6\n"PollEventParameters_ActionFinished\x12\x10\n\x08\x61\x63tionID\x18\x01 \x01(\r"n\n\x13PollEventParameters\x12M\n\x0e\x61\x63tionFinished\x18\x01 \x01(\x0b\x32\x33.Askui.API.TDKv1.PollEventParameters_ActionFinishedH\x00\x42\x08\n\x06\x64\x61taOf"-\n\x15\x41\x63tionParameters_Wait\x12\x14\n\x0cmilliseconds\x18\x01 \x01(\r"W\n"ActionParameters_MouseButton_Press\x12\x31\n\x0bmouseButton\x18\x01 \x01(\x0e\x32\x1c.Askui.API.TDKv1.MouseButton"Y\n$ActionParameters_MouseButton_Release\x12\x31\n\x0bmouseButton\x18\x01 \x01(\x0e\x32\x1c.Askui.API.TDKv1.MouseButton"p\n,ActionParameters_MouseButton_PressAndRelease\x12\x31\n\x0bmouseButton\x18\x01 \x01(\x0e\x32\x1c.Askui.API.TDKv1.MouseButton\x12\r\n\x05\x63ount\x18\x02 \x01(\r"\xc0\x01\n!ActionParameters_MouseWheelScroll\x12=\n\tdirection\x18\x01 \x01(\x0e\x32*.Askui.API.TDKv1.MouseWheelScrollDirection\x12\x37\n\tdeltaType\x18\x02 \x01(\x0e\x32$.Askui.API.TDKv1.MouseWheelDeltaType\x12\r\n\x05\x64\x65lta\x18\x03 \x01(\x05\x12\x14\n\x0cmilliseconds\x18\x04 \x01(\x05"x\n\x1a\x41\x63tionParameters_MouseMove\x12.\n\x08position\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.Coordinate2\x12\x19\n\x0cmilliseconds\x18\x02 \x01(\rH\x00\x88\x01\x01\x42\x0f\n\r_milliseconds"v\n ActionParameters_MouseMove_Delta\x12&\n\x05\x64\x65lta\x18\x01 \x01(\x0b\x32\x17.Askui.API.TDKv1.Delta2\x12\x19\n\x0cmilliseconds\x18\x02 \x01(\rH\x00\x88\x01\x01\x42\x0f\n\r_milliseconds"O\n"ActionParameters_KeyboardKey_Press\x12\x0f\n\x07keyName\x18\x01 \x01(\t\x12\x18\n\x10modifierKeyNames\x18\x02 \x03(\t"Q\n$ActionParameters_KeyboardKey_Release\x12\x0f\n\x07keyName\x18\x01 \x01(\t\x12\x18\n\x10modifierKeyNames\x18\x02 \x03(\t"Y\n,ActionParameters_KeyboardKey_PressAndRelease\x12\x0f\n\x07keyName\x18\x01 \x01(\t\x12\x18\n\x10modifierKeyNames\x18\x02 \x03(\t"Q\n#ActionParameters_KeyboardKeys_Press\x12\x10\n\x08keyNames\x18\x01 \x03(\t\x12\x18\n\x10modifierKeyNames\x18\x02 \x03(\t"S\n%ActionParameters_KeyboardKeys_Release\x12\x10\n\x08keyNames\x18\x01 \x03(\t\x12\x18\n\x10modifierKeyNames\x18\x02 \x03(\t"[\n-ActionParameters_KeyboardKeys_PressAndRelease\x12\x10\n\x08keyNames\x18\x01 \x03(\t\x12\x18\n\x10modifierKeyNames\x18\x02 \x03(\t"\x99\x01\n"ActionParameters_KeyboardType_Text\x12\x0c\n\x04text\x18\x01 \x01(\t\x12;\n\x10typingSpeedValue\x18\x02 \x01(\x0e\x32!.Askui.API.TDKv1.TypingSpeedValue\x12\x18\n\x0btypingSpeed\x18\x03 \x01(\rH\x00\x88\x01\x01\x42\x0e\n\x0c_typingSpeed"\xa0\x01\n)ActionParameters_KeyboardType_UnicodeText\x12\x0c\n\x04text\x18\x01 \x01(\x0c\x12;\n\x10typingSpeedValue\x18\x02 \x01(\x0e\x32!.Askui.API.TDKv1.TypingSpeedValue\x12\x18\n\x0btypingSpeed\x18\x03 \x01(\rH\x00\x88\x01\x01\x42\x0e\n\x0c_typingSpeed"l\n\x1b\x41\x63tionParameters_RunCommand\x12\x0f\n\x07\x63ommand\x18\x01 \x01(\t\x12"\n\x15timeoutInMilliseconds\x18\x02 \x01(\rH\x00\x88\x01\x01\x42\x18\n\x16_timeoutInMilliseconds"\xf5\n\n\x10\x41\x63tionParameters\x12%\n\x04none\x18\x01 \x01(\x0b\x32\x15.Askui.API.TDKv1.VoidH\x00\x12\x36\n\x04wait\x18\x02 \x01(\x0b\x32&.Askui.API.TDKv1.ActionParameters_WaitH\x00\x12O\n\x10mouseButtonPress\x18\x03 \x01(\x0b\x32\x33.Askui.API.TDKv1.ActionParameters_MouseButton_PressH\x00\x12S\n\x12mouseButtonRelease\x18\x04 \x01(\x0b\x32\x35.Askui.API.TDKv1.ActionParameters_MouseButton_ReleaseH\x00\x12\x63\n\x1amouseButtonPressAndRelease\x18\x05 \x01(\x0b\x32=.Askui.API.TDKv1.ActionParameters_MouseButton_PressAndReleaseH\x00\x12N\n\x10mouseWheelScroll\x18\x06 \x01(\x0b\x32\x32.Askui.API.TDKv1.ActionParameters_MouseWheelScrollH\x00\x12@\n\tmouseMove\x18\x07 \x01(\x0b\x32+.Askui.API.TDKv1.ActionParameters_MouseMoveH\x00\x12K\n\x0emouseMoveDelta\x18\x08 \x01(\x0b\x32\x31.Askui.API.TDKv1.ActionParameters_MouseMove_DeltaH\x00\x12O\n\x10keyboardKeyPress\x18\t \x01(\x0b\x32\x33.Askui.API.TDKv1.ActionParameters_KeyboardKey_PressH\x00\x12S\n\x12keyboardKeyRelease\x18\n \x01(\x0b\x32\x35.Askui.API.TDKv1.ActionParameters_KeyboardKey_ReleaseH\x00\x12\x63\n\x1akeyboardKeyPressAndRelease\x18\x0b \x01(\x0b\x32=.Askui.API.TDKv1.ActionParameters_KeyboardKey_PressAndReleaseH\x00\x12Q\n\x11keyboardKeysPress\x18\x0c \x01(\x0b\x32\x34.Askui.API.TDKv1.ActionParameters_KeyboardKeys_PressH\x00\x12U\n\x13keyboardKeysRelease\x18\r \x01(\x0b\x32\x36.Askui.API.TDKv1.ActionParameters_KeyboardKeys_ReleaseH\x00\x12\x65\n\x1bkeyboardKeysPressAndRelease\x18\x0e \x01(\x0b\x32>.Askui.API.TDKv1.ActionParameters_KeyboardKeys_PressAndReleaseH\x00\x12O\n\x10keyboardTypeText\x18\x0f \x01(\x0b\x32\x33.Askui.API.TDKv1.ActionParameters_KeyboardType_TextH\x00\x12]\n\x17keyboardTypeUnicodeText\x18\x10 \x01(\x0b\x32:.Askui.API.TDKv1.ActionParameters_KeyboardType_UnicodeTextH\x00\x12\x42\n\nruncommand\x18\x11 \x01(\x0b\x32,.Askui.API.TDKv1.ActionParameters_RunCommandH\x00\x42\x08\n\x06\x64\x61taOf"G\n\x14Request_StartSession\x12\x13\n\x0bsessionGUID\x18\x01 \x01(\t\x12\x1a\n\x12immediateExecution\x18\x02 \x01(\x08"J\n\x15Response_StartSession\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo"G\n\x12Request_EndSession\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo"t\n\x0cRequest_Poll\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo\x12\x31\n\x0bpollEventID\x18\x02 \x01(\x0e\x32\x1c.Askui.API.TDKv1.PollEventID"K\n\x16Request_StartExecution\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo"J\n\x15Request_StopExecution\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo"\x85\x01\n\rResponse_Poll\x12\x31\n\x0bpollEventID\x18\x01 \x01(\x0e\x32\x1c.Askui.API.TDKv1.PollEventID\x12\x41\n\x13pollEventParameters\x18\x02 \x01(\x0b\x32$.Askui.API.TDKv1.PollEventParameters"\xc2\x01\n\x19Request_RunRecordedAction\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo\x12\x35\n\ractionClassID\x18\x02 \x01(\x0e\x32\x1e.Askui.API.TDKv1.ActionClassID\x12;\n\x10\x61\x63tionParameters\x18\x03 \x01(\x0b\x32!.Askui.API.TDKv1.ActionParameters"L\n\x1aResponse_RunRecordedAction\x12\x10\n\x08\x61\x63tionID\x18\x01 \x01(\r\x12\x1c\n\x14requiredMilliseconds\x18\x02 \x01(\r"\xc6\x01\n\x1dRequest_ScheduleBatchedAction\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo\x12\x35\n\ractionClassID\x18\x02 \x01(\x0e\x32\x1e.Askui.API.TDKv1.ActionClassID\x12;\n\x10\x61\x63tionParameters\x18\x03 \x01(\x0b\x32!.Askui.API.TDKv1.ActionParameters"2\n\x1eResponse_ScheduleBatchedAction\x12\x10\n\x08\x61\x63tionID\x18\x01 \x01(\r"K\n\x16Request_GetActionCount\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo".\n\x17Response_GetActionCount\x12\x13\n\x0b\x61\x63tionCount\x18\x01 \x01(\r"[\n\x11Request_GetAction\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo\x12\x13\n\x0b\x61\x63tionIndex\x18\x02 \x01(\r"\x9a\x01\n\x12Response_GetAction\x12\x10\n\x08\x61\x63tionID\x18\x01 \x01(\r\x12\x35\n\ractionClassID\x18\x02 \x01(\x0e\x32\x1e.Askui.API.TDKv1.ActionClassID\x12;\n\x10\x61\x63tionParameters\x18\x03 \x01(\x0b\x32!.Askui.API.TDKv1.ActionParameters"[\n\x14Request_RemoveAction\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo\x12\x10\n\x08\x61\x63tionID\x18\x02 \x01(\r"M\n\x18Request_RemoveAllActions\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo"J\n\x15Request_StartBatchRun\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo"I\n\x14Request_StopBatchRun\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo"\xa4\x01\n\x15Request_CaptureScreen\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo\x12\x42\n\x11\x63\x61ptureParameters\x18\x02 \x01(\x0b\x32".Askui.API.TDKv1.CaptureParametersH\x00\x88\x01\x01\x42\x14\n\x12_captureParameters"A\n\x16Response_CaptureScreen\x12\'\n\x06\x62itmap\x18\x01 \x01(\x0b\x32\x17.Askui.API.TDKv1.Bitmap"O\n$Response_GetContinuousCapturedScreen\x12\'\n\x06\x62itmap\x18\x01 \x01(\x0b\x32\x17.Askui.API.TDKv1.Bitmap"\xde\x01\n\x1cReuqest_SetTestConfiguration\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo\x12\x44\n\x18\x64\x65\x66\x61ultCaptureParameters\x18\x02 \x01(\x0b\x32".Askui.API.TDKv1.CaptureParameters\x12 \n\x18mouseDelayInMilliseconds\x18\x03 \x01(\r\x12#\n\x1bkeyboardDelayInMilliseconds\x18\x04 \x01(\r"g\n\x15Request_SetMouseDelay\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo\x12\x1b\n\x13\x64\x65layInMilliseconds\x18\x02 \x01(\r"j\n\x18Request_SetKeyboardDelay\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo\x12\x1b\n\x13\x64\x65layInMilliseconds\x18\x02 \x01(\r"\x9f\x01\n\x12\x44isplayInformation\x12\x11\n\tdisplayID\x18\x01 \x01(\r\x12\x0c\n\x04name\x18\x02 \x01(\t\x12,\n\x0csizeInPixels\x18\x03 \x01(\x0b\x32\x16.Askui.API.TDKv1.Size2\x12:\n\x16virtualScreenRectangle\x18\x04 \x01(\x0b\x32\x1a.Askui.API.TDKv1.Rectangle"\x93\x01\n\x1eResponse_GetDisplayInformation\x12\x35\n\x08\x64isplays\x18\x01 \x03(\x0b\x32#.Askui.API.TDKv1.DisplayInformation\x12:\n\x16virtualScreenRectangle\x18\x02 \x01(\x0b\x32\x1a.Askui.API.TDKv1.Rectangle"1\n\x19Response_GetMousePosition\x12\t\n\x01x\x18\x01 \x01(\x05\x12\t\n\x01y\x18\x02 \x01(\x05"(\n\x13ProcessInfoExtended\x12\x11\n\thasWindow\x18\x01 \x01(\x08"y\n\x0bProcessInfo\x12\n\n\x02ID\x18\x01 \x01(\x04\x12\x0c\n\x04name\x18\x02 \x01(\t\x12?\n\x0c\x65xtendedInfo\x18\x03 \x01(\x0b\x32$.Askui.API.TDKv1.ProcessInfoExtendedH\x00\x88\x01\x01\x42\x0f\n\r_extendedInfo"1\n\x16Request_GetProcessList\x12\x17\n\x0fgetExtendedInfo\x18\x01 \x01(\x08"J\n\x17Response_GetProcessList\x12/\n\tprocesses\x18\x01 \x03(\x0b\x32\x1c.Askui.API.TDKv1.ProcessInfo"*\n\x15Request_GetWindowList\x12\x11\n\tprocessID\x18\x01 \x01(\x04"&\n\nWindowInfo\x12\n\n\x02ID\x18\x01 \x01(\x04\x12\x0c\n\x04name\x18\x02 \x01(\t"F\n\x16Response_GetWindowList\x12,\n\x07windows\x18\x01 \x03(\x0b\x32\x1b.Askui.API.TDKv1.WindowInfo"-\n\x18Request_SetActiveDisplay\x12\x11\n\tdisplayID\x18\x01 \x01(\r">\n\x17Request_SetActiveWindow\x12\x11\n\tprocessID\x18\x01 \x01(\x04\x12\x10\n\x08windowID\x18\x02 \x01(\x04"q\n\x10\x41utomationTarget\x12\n\n\x02ID\x18\x01 \x01(\x04\x12\x33\n\x04type\x18\x02 \x01(\x0e\x32%.Askui.API.TDKv1.AutomationTargetType\x12\x0c\n\x04name\x18\x03 \x01(\t\x12\x0e\n\x06\x61\x63tive\x18\x04 \x01(\x08"V\n Response_GetAutomationTargetList\x12\x32\n\x07targets\x18\x01 \x03(\x0b\x32!.Askui.API.TDKv1.AutomationTarget"/\n!Request_SetActiveAutomationTarget\x12\n\n\x02ID\x18\x01 \x01(\x04"Q\n\x10Request_GetColor\x12\t\n\x01x\x18\x01 \x01(\x05\x12\t\n\x01y\x18\x02 \x01(\x05\x12\'\n\x06\x62itmap\x18\x03 \x01(\x0b\x32\x17.Askui.API.TDKv1.Bitmap":\n\x11Response_GetColor\x12%\n\x05\x63olor\x18\x01 \x01(\x0b\x32\x16.Askui.API.TDKv1.Color"-\n\x15Request_GetPixelColor\x12\t\n\x01x\x18\x01 \x01(\x05\x12\t\n\x01y\x18\x02 \x01(\x05"?\n\x16Response_GetPixelColor\x12%\n\x05\x63olor\x18\x01 \x01(\x0b\x32\x16.Askui.API.TDKv1.Color"n\n\x17Request_SetDisplayLabel\x12\x31\n\x0bsessionInfo\x18\x01 \x01(\x0b\x32\x1c.Askui.API.TDKv1.SessionInfo\x12\x11\n\tdisplayID\x18\x02 \x01(\r\x12\r\n\x05label\x18\x03 \x01(\t*N\n\x0bPollEventID\x12\x19\n\x15PollEventID_Undefined\x10\x00\x12\x1e\n\x1aPollEventID_ActionFinished\x10\x02"\x04\x08\x01\x10\x01*m\n\x0bMouseButton\x12\x19\n\x15MouseButton_Undefined\x10\x00\x12\x14\n\x10MouseButton_Left\x10\x01\x12\x15\n\x11MouseButton_Right\x10\x02\x12\x16\n\x12MouseButton_Middle\x10\x03*\x8b\x05\n\rActionClassID\x12\x1b\n\x17\x41\x63tionClassID_Undefined\x10\x00\x12\x16\n\x12\x41\x63tionClassID_Wait\x10\x01\x12#\n\x1f\x41\x63tionClassID_MouseButton_Press\x10\x08\x12%\n!ActionClassID_MouseButton_Release\x10\t\x12-\n)ActionClassID_MouseButton_PressAndRelease\x10\n\x12"\n\x1e\x41\x63tionClassID_MouseWheelScroll\x10\x0b\x12\x1b\n\x17\x41\x63tionClassID_MouseMove\x10\x0c\x12!\n\x1d\x41\x63tionClassID_MouseMove_Delta\x10\r\x12#\n\x1f\x41\x63tionClassID_KeyboardKey_Press\x10\x0e\x12%\n!ActionClassID_KeyboardKey_Release\x10\x0f\x12-\n)ActionClassID_KeyboardKey_PressAndRelease\x10\x10\x12$\n ActionClassID_KeyboardKeys_Press\x10\x11\x12&\n"ActionClassID_KeyboardKeys_Release\x10\x12\x12.\n*ActionClassID_KeyboardKeys_PressAndRelease\x10\x13\x12#\n\x1f\x41\x63tionClassID_KeyboardType_Text\x10\x14\x12*\n&ActionClassID_KeyboardType_UnicodeText\x10\x15\x12\x1c\n\x18\x41\x63tionClassID_RunCommand\x10\x16*i\n\x13MouseWheelDeltaType\x12\x1d\n\x19MouseWheelDelta_Undefined\x10\x00\x12\x17\n\x13MouseWheelDelta_Raw\x10\x01\x12\x1a\n\x16MouseWheelDelta_Detent\x10\x02*\x96\x01\n\x19MouseWheelScrollDirection\x12\'\n#MouseWheelScrollDirection_Undefined\x10\x00\x12&\n"MouseWheelScrollDirection_Vertical\x10\x01\x12(\n$MouseWheelScrollDirection_Horizontal\x10\x02*z\n\x10TypingSpeedValue\x12\x1e\n\x1aTypingSpeedValue_Undefined\x10\x00\x12(\n$TypingSpeedValue_CharactersPerSecond\x10\x01\x12\x1c\n\x18TypingSpeedValue_Seconds\x10\x02*S\n\x14\x41utomationTargetType\x12\x1a\n\x16\x41utomationTarget_Local\x10\x00\x12\x1f\n\x1b\x41utomationTarget_Background\x10\x01\x32\xb9\x15\n\rControllerAPI\x12_\n\x0cStartSession\x12%.Askui.API.TDKv1.Request_StartSession\x1a&.Askui.API.TDKv1.Response_StartSession"\x00\x12S\n\nEndSession\x12#.Askui.API.TDKv1.Request_EndSession\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12G\n\x04Poll\x12\x1d.Askui.API.TDKv1.Request_Poll\x1a\x1e.Askui.API.TDKv1.Response_Poll"\x00\x12[\n\x0eStartExecution\x12\'.Askui.API.TDKv1.Request_StartExecution\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12Y\n\rStopExecution\x12&.Askui.API.TDKv1.Request_StopExecution\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12n\n\x11RunRecordedAction\x12*.Askui.API.TDKv1.Request_RunRecordedAction\x1a+.Askui.API.TDKv1.Response_RunRecordedAction"\x00\x12z\n\x15ScheduleBatchedAction\x12..Askui.API.TDKv1.Request_ScheduleBatchedAction\x1a/.Askui.API.TDKv1.Response_ScheduleBatchedAction"\x00\x12Y\n\rStartBatchRun\x12&.Askui.API.TDKv1.Request_StartBatchRun\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12W\n\x0cStopBatchRun\x12%.Askui.API.TDKv1.Request_StopBatchRun\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12\x65\n\x0eGetActionCount\x12\'.Askui.API.TDKv1.Request_GetActionCount\x1a(.Askui.API.TDKv1.Response_GetActionCount"\x00\x12V\n\tGetAction\x12".Askui.API.TDKv1.Request_GetAction\x1a#.Askui.API.TDKv1.Response_GetAction"\x00\x12W\n\x0cRemoveAction\x12%.Askui.API.TDKv1.Request_RemoveAction\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12_\n\x10RemoveAllActions\x12).Askui.API.TDKv1.Request_RemoveAllActions\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12\x62\n\rCaptureScreen\x12&.Askui.API.TDKv1.Request_CaptureScreen\x1a\'.Askui.API.TDKv1.Response_CaptureScreen"\x00\x12g\n\x14SetTestConfiguration\x12-.Askui.API.TDKv1.Reuqest_SetTestConfiguration\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12Y\n\rSetMouseDelay\x12&.Askui.API.TDKv1.Request_SetMouseDelay\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12_\n\x10SetKeyboardDelay\x12).Askui.API.TDKv1.Request_SetKeyboardDelay\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12i\n\x15GetDisplayInformation\x12\x1d.Askui.API.TDKv1.Request_Void\x1a/.Askui.API.TDKv1.Response_GetDisplayInformation"\x00\x12_\n\x10GetMousePosition\x12\x1d.Askui.API.TDKv1.Request_Void\x1a*.Askui.API.TDKv1.Response_GetMousePosition"\x00\x12\x65\n\x0eGetProcessList\x12\'.Askui.API.TDKv1.Request_GetProcessList\x1a(.Askui.API.TDKv1.Response_GetProcessList"\x00\x12\x62\n\rGetWindowList\x12&.Askui.API.TDKv1.Request_GetWindowList\x1a\'.Askui.API.TDKv1.Response_GetWindowList"\x00\x12m\n\x17GetAutomationTargetList\x12\x1d.Askui.API.TDKv1.Request_Void\x1a\x31.Askui.API.TDKv1.Response_GetAutomationTargetList"\x00\x12_\n\x10SetActiveDisplay\x12).Askui.API.TDKv1.Request_SetActiveDisplay\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12]\n\x0fSetActiveWindow\x12(.Askui.API.TDKv1.Request_SetActiveWindow\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12q\n\x19SetActiveAutomationTarget\x12\x32.Askui.API.TDKv1.Request_SetActiveAutomationTarget\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x12S\n\x08GetColor\x12!.Askui.API.TDKv1.Request_GetColor\x1a".Askui.API.TDKv1.Response_GetColor"\x00\x12\x62\n\rGetPixelColor\x12&.Askui.API.TDKv1.Request_GetPixelColor\x1a\'.Askui.API.TDKv1.Response_GetPixelColor"\x00\x12]\n\x0fSetDisplayLabel\x12(.Askui.API.TDKv1.Request_SetDisplayLabel\x1a\x1e.Askui.API.TDKv1.Response_Void"\x00\x62\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "Controller_V1_pb2", _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals["_POLLEVENTID"]._serialized_start = 8218
    _globals["_POLLEVENTID"]._serialized_end = 8296
    _globals["_MOUSEBUTTON"]._serialized_start = 8298
    _globals["_MOUSEBUTTON"]._serialized_end = 8407
    _globals["_ACTIONCLASSID"]._serialized_start = 8410
    _globals["_ACTIONCLASSID"]._serialized_end = 9061
    _globals["_MOUSEWHEELDELTATYPE"]._serialized_start = 9063
    _globals["_MOUSEWHEELDELTATYPE"]._serialized_end = 9168
    _globals["_MOUSEWHEELSCROLLDIRECTION"]._serialized_start = 9171
    _globals["_MOUSEWHEELSCROLLDIRECTION"]._serialized_end = 9321
    _globals["_TYPINGSPEEDVALUE"]._serialized_start = 9323
    _globals["_TYPINGSPEEDVALUE"]._serialized_end = 9445
    _globals["_AUTOMATIONTARGETTYPE"]._serialized_start = 9447
    _globals["_AUTOMATIONTARGETTYPE"]._serialized_end = 9530
    _globals["_VOID"]._serialized_start = 40
    _globals["_VOID"]._serialized_end = 46
    _globals["_REQUEST_VOID"]._serialized_start = 48
    _globals["_REQUEST_VOID"]._serialized_end = 62
    _globals["_RESPONSE_VOID"]._serialized_start = 64
    _globals["_RESPONSE_VOID"]._serialized_end = 79
    _globals["_SIZE2"]._serialized_start = 81
    _globals["_SIZE2"]._serialized_end = 119
    _globals["_DELTA2"]._serialized_start = 121
    _globals["_DELTA2"]._serialized_end = 151
    _globals["_COORDINATE2"]._serialized_start = 153
    _globals["_COORDINATE2"]._serialized_end = 188
    _globals["_RECTANGLE"]._serialized_start = 190
    _globals["_RECTANGLE"]._serialized_end = 259
    _globals["_BITMAP"]._serialized_start = 261
    _globals["_BITMAP"]._serialized_end = 378
    _globals["_COLOR"]._serialized_start = 380
    _globals["_COLOR"]._serialized_end = 420
    _globals["_GUID"]._serialized_start = 422
    _globals["_GUID"]._serialized_end = 463
    _globals["_SESSIONINFO"]._serialized_start = 465
    _globals["_SESSIONINFO"]._serialized_end = 541
    _globals["_CAPTUREAREA"]._serialized_start = 543
    _globals["_CAPTUREAREA"]._serialized_end = 644
    _globals["_CAPTUREPARAMETERS"]._serialized_start = 647
    _globals["_CAPTUREPARAMETERS"]._serialized_end = 776
    _globals["_POLLEVENTPARAMETERS_ACTIONFINISHED"]._serialized_start = 778
    _globals["_POLLEVENTPARAMETERS_ACTIONFINISHED"]._serialized_end = 832
    _globals["_POLLEVENTPARAMETERS"]._serialized_start = 834
    _globals["_POLLEVENTPARAMETERS"]._serialized_end = 944
    _globals["_ACTIONPARAMETERS_WAIT"]._serialized_start = 946
    _globals["_ACTIONPARAMETERS_WAIT"]._serialized_end = 991
    _globals["_ACTIONPARAMETERS_MOUSEBUTTON_PRESS"]._serialized_start = 993
    _globals["_ACTIONPARAMETERS_MOUSEBUTTON_PRESS"]._serialized_end = 1080
    _globals["_ACTIONPARAMETERS_MOUSEBUTTON_RELEASE"]._serialized_start = 1082
    _globals["_ACTIONPARAMETERS_MOUSEBUTTON_RELEASE"]._serialized_end = 1171
    _globals["_ACTIONPARAMETERS_MOUSEBUTTON_PRESSANDRELEASE"]._serialized_start = 1173
    _globals["_ACTIONPARAMETERS_MOUSEBUTTON_PRESSANDRELEASE"]._serialized_end = 1285
    _globals["_ACTIONPARAMETERS_MOUSEWHEELSCROLL"]._serialized_start = 1288
    _globals["_ACTIONPARAMETERS_MOUSEWHEELSCROLL"]._serialized_end = 1480
    _globals["_ACTIONPARAMETERS_MOUSEMOVE"]._serialized_start = 1482
    _globals["_ACTIONPARAMETERS_MOUSEMOVE"]._serialized_end = 1602
    _globals["_ACTIONPARAMETERS_MOUSEMOVE_DELTA"]._serialized_start = 1604
    _globals["_ACTIONPARAMETERS_MOUSEMOVE_DELTA"]._serialized_end = 1722
    _globals["_ACTIONPARAMETERS_KEYBOARDKEY_PRESS"]._serialized_start = 1724
    _globals["_ACTIONPARAMETERS_KEYBOARDKEY_PRESS"]._serialized_end = 1803
    _globals["_ACTIONPARAMETERS_KEYBOARDKEY_RELEASE"]._serialized_start = 1805
    _globals["_ACTIONPARAMETERS_KEYBOARDKEY_RELEASE"]._serialized_end = 1886
    _globals["_ACTIONPARAMETERS_KEYBOARDKEY_PRESSANDRELEASE"]._serialized_start = 1888
    _globals["_ACTIONPARAMETERS_KEYBOARDKEY_PRESSANDRELEASE"]._serialized_end = 1977
    _globals["_ACTIONPARAMETERS_KEYBOARDKEYS_PRESS"]._serialized_start = 1979
    _globals["_ACTIONPARAMETERS_KEYBOARDKEYS_PRESS"]._serialized_end = 2060
    _globals["_ACTIONPARAMETERS_KEYBOARDKEYS_RELEASE"]._serialized_start = 2062
    _globals["_ACTIONPARAMETERS_KEYBOARDKEYS_RELEASE"]._serialized_end = 2145
    _globals["_ACTIONPARAMETERS_KEYBOARDKEYS_PRESSANDRELEASE"]._serialized_start = 2147
    _globals["_ACTIONPARAMETERS_KEYBOARDKEYS_PRESSANDRELEASE"]._serialized_end = 2238
    _globals["_ACTIONPARAMETERS_KEYBOARDTYPE_TEXT"]._serialized_start = 2241
    _globals["_ACTIONPARAMETERS_KEYBOARDTYPE_TEXT"]._serialized_end = 2394
    _globals["_ACTIONPARAMETERS_KEYBOARDTYPE_UNICODETEXT"]._serialized_start = 2397
    _globals["_ACTIONPARAMETERS_KEYBOARDTYPE_UNICODETEXT"]._serialized_end = 2557
    _globals["_ACTIONPARAMETERS_RUNCOMMAND"]._serialized_start = 2559
    _globals["_ACTIONPARAMETERS_RUNCOMMAND"]._serialized_end = 2667
    _globals["_ACTIONPARAMETERS"]._serialized_start = 2670
    _globals["_ACTIONPARAMETERS"]._serialized_end = 4067
    _globals["_REQUEST_STARTSESSION"]._serialized_start = 4069
    _globals["_REQUEST_STARTSESSION"]._serialized_end = 4140
    _globals["_RESPONSE_STARTSESSION"]._serialized_start = 4142
    _globals["_RESPONSE_STARTSESSION"]._serialized_end = 4216
    _globals["_REQUEST_ENDSESSION"]._serialized_start = 4218
    _globals["_REQUEST_ENDSESSION"]._serialized_end = 4289
    _globals["_REQUEST_POLL"]._serialized_start = 4291
    _globals["_REQUEST_POLL"]._serialized_end = 4407
    _globals["_REQUEST_STARTEXECUTION"]._serialized_start = 4409
    _globals["_REQUEST_STARTEXECUTION"]._serialized_end = 4484
    _globals["_REQUEST_STOPEXECUTION"]._serialized_start = 4486
    _globals["_REQUEST_STOPEXECUTION"]._serialized_end = 4560
    _globals["_RESPONSE_POLL"]._serialized_start = 4563
    _globals["_RESPONSE_POLL"]._serialized_end = 4696
    _globals["_REQUEST_RUNRECORDEDACTION"]._serialized_start = 4699
    _globals["_REQUEST_RUNRECORDEDACTION"]._serialized_end = 4893
    _globals["_RESPONSE_RUNRECORDEDACTION"]._serialized_start = 4895
    _globals["_RESPONSE_RUNRECORDEDACTION"]._serialized_end = 4971
    _globals["_REQUEST_SCHEDULEBATCHEDACTION"]._serialized_start = 4974
    _globals["_REQUEST_SCHEDULEBATCHEDACTION"]._serialized_end = 5172
    _globals["_RESPONSE_SCHEDULEBATCHEDACTION"]._serialized_start = 5174
    _globals["_RESPONSE_SCHEDULEBATCHEDACTION"]._serialized_end = 5224
    _globals["_REQUEST_GETACTIONCOUNT"]._serialized_start = 5226
    _globals["_REQUEST_GETACTIONCOUNT"]._serialized_end = 5301
    _globals["_RESPONSE_GETACTIONCOUNT"]._serialized_start = 5303
    _globals["_RESPONSE_GETACTIONCOUNT"]._serialized_end = 5349
    _globals["_REQUEST_GETACTION"]._serialized_start = 5351
    _globals["_REQUEST_GETACTION"]._serialized_end = 5442
    _globals["_RESPONSE_GETACTION"]._serialized_start = 5445
    _globals["_RESPONSE_GETACTION"]._serialized_end = 5599
    _globals["_REQUEST_REMOVEACTION"]._serialized_start = 5601
    _globals["_REQUEST_REMOVEACTION"]._serialized_end = 5692
    _globals["_REQUEST_REMOVEALLACTIONS"]._serialized_start = 5694
    _globals["_REQUEST_REMOVEALLACTIONS"]._serialized_end = 5771
    _globals["_REQUEST_STARTBATCHRUN"]._serialized_start = 5773
    _globals["_REQUEST_STARTBATCHRUN"]._serialized_end = 5847
    _globals["_REQUEST_STOPBATCHRUN"]._serialized_start = 5849
    _globals["_REQUEST_STOPBATCHRUN"]._serialized_end = 5922
    _globals["_REQUEST_CAPTURESCREEN"]._serialized_start = 5925
    _globals["_REQUEST_CAPTURESCREEN"]._serialized_end = 6089
    _globals["_RESPONSE_CAPTURESCREEN"]._serialized_start = 6091
    _globals["_RESPONSE_CAPTURESCREEN"]._serialized_end = 6156
    _globals["_RESPONSE_GETCONTINUOUSCAPTUREDSCREEN"]._serialized_start = 6158
    _globals["_RESPONSE_GETCONTINUOUSCAPTUREDSCREEN"]._serialized_end = 6237
    _globals["_REUQEST_SETTESTCONFIGURATION"]._serialized_start = 6240
    _globals["_REUQEST_SETTESTCONFIGURATION"]._serialized_end = 6462
    _globals["_REQUEST_SETMOUSEDELAY"]._serialized_start = 6464
    _globals["_REQUEST_SETMOUSEDELAY"]._serialized_end = 6567
    _globals["_REQUEST_SETKEYBOARDDELAY"]._serialized_start = 6569
    _globals["_REQUEST_SETKEYBOARDDELAY"]._serialized_end = 6675
    _globals["_DISPLAYINFORMATION"]._serialized_start = 6678
    _globals["_DISPLAYINFORMATION"]._serialized_end = 6837
    _globals["_RESPONSE_GETDISPLAYINFORMATION"]._serialized_start = 6840
    _globals["_RESPONSE_GETDISPLAYINFORMATION"]._serialized_end = 6987
    _globals["_RESPONSE_GETMOUSEPOSITION"]._serialized_start = 6989
    _globals["_RESPONSE_GETMOUSEPOSITION"]._serialized_end = 7038
    _globals["_PROCESSINFOEXTENDED"]._serialized_start = 7040
    _globals["_PROCESSINFOEXTENDED"]._serialized_end = 7080
    _globals["_PROCESSINFO"]._serialized_start = 7082
    _globals["_PROCESSINFO"]._serialized_end = 7203
    _globals["_REQUEST_GETPROCESSLIST"]._serialized_start = 7205
    _globals["_REQUEST_GETPROCESSLIST"]._serialized_end = 7254
    _globals["_RESPONSE_GETPROCESSLIST"]._serialized_start = 7256
    _globals["_RESPONSE_GETPROCESSLIST"]._serialized_end = 7330
    _globals["_REQUEST_GETWINDOWLIST"]._serialized_start = 7332
    _globals["_REQUEST_GETWINDOWLIST"]._serialized_end = 7374
    _globals["_WINDOWINFO"]._serialized_start = 7376
    _globals["_WINDOWINFO"]._serialized_end = 7414
    _globals["_RESPONSE_GETWINDOWLIST"]._serialized_start = 7416
    _globals["_RESPONSE_GETWINDOWLIST"]._serialized_end = 7486
    _globals["_REQUEST_SETACTIVEDISPLAY"]._serialized_start = 7488
    _globals["_REQUEST_SETACTIVEDISPLAY"]._serialized_end = 7533
    _globals["_REQUEST_SETACTIVEWINDOW"]._serialized_start = 7535
    _globals["_REQUEST_SETACTIVEWINDOW"]._serialized_end = 7597
    _globals["_AUTOMATIONTARGET"]._serialized_start = 7599
    _globals["_AUTOMATIONTARGET"]._serialized_end = 7712
    _globals["_RESPONSE_GETAUTOMATIONTARGETLIST"]._serialized_start = 7714
    _globals["_RESPONSE_GETAUTOMATIONTARGETLIST"]._serialized_end = 7800
    _globals["_REQUEST_SETACTIVEAUTOMATIONTARGET"]._serialized_start = 7802
    _globals["_REQUEST_SETACTIVEAUTOMATIONTARGET"]._serialized_end = 7849
    _globals["_REQUEST_GETCOLOR"]._serialized_start = 7851
    _globals["_REQUEST_GETCOLOR"]._serialized_end = 7932
    _globals["_RESPONSE_GETCOLOR"]._serialized_start = 7934
    _globals["_RESPONSE_GETCOLOR"]._serialized_end = 7992
    _globals["_REQUEST_GETPIXELCOLOR"]._serialized_start = 7994
    _globals["_REQUEST_GETPIXELCOLOR"]._serialized_end = 8039
    _globals["_RESPONSE_GETPIXELCOLOR"]._serialized_start = 8041
    _globals["_RESPONSE_GETPIXELCOLOR"]._serialized_end = 8104
    _globals["_REQUEST_SETDISPLAYLABEL"]._serialized_start = 8106
    _globals["_REQUEST_SETDISPLAYLABEL"]._serialized_end = 8216
    _globals["_CONTROLLERAPI"]._serialized_start = 9533
    _globals["_CONTROLLERAPI"]._serialized_end = 12278
# @@protoc_insertion_point(module_scope)
