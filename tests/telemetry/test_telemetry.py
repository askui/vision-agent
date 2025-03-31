import pytest

from askui.telemetry.processors import InMemoryProcessor
from askui.telemetry.telemetry import Telemetry, TelemetrySettings


def test_telemetry_disabled():
    settings = TelemetrySettings(enabled=False)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    @telemetry.track_call()
    def test_func(x: int) -> int:
        return x * 2

    result = test_func(5)
    assert result == 10
    assert len(processor.get_events()) == 0


def test_telemetry_enabled():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    @telemetry.track_call(include_first_arg=True)
    def test_func(x: int) -> int:
        return x * 2

    result = test_func(5)
    assert result == 10

    events = processor.get_events()
    assert len(events) == 2

    start_event = events[0]
    assert start_event.event_type == "method_started"
    assert start_event.method_name.endswith("test_func")
    assert start_event.args == (5,)
    assert start_event.kwargs == {}

    end_event = events[1]
    assert end_event.event_type == "method_ended"
    assert end_event.method_name.endswith("test_func")
    assert end_event.args == (5,)
    assert end_event.kwargs == {}
    assert end_event.response == 10
    assert end_event.duration_ms is not None
    assert end_event.duration_ms >= 0


def test_telemetry_error():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    @telemetry.track_call(include_first_arg=True)
    def test_func(x: int) -> int:
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        test_func(5)

    events = processor.get_events()
    assert len(events) == 2

    start_event = events[0]
    assert start_event.event_type == "method_started"
    assert start_event.method_name.endswith("test_func")
    assert start_event.args == (5,)
    assert start_event.kwargs == {}

    error_event = events[1]
    assert error_event.event_type == "error_occurred"
    assert error_event.method_name.endswith("test_func")
    assert error_event.args == (5,)
    assert error_event.kwargs == {}
    assert isinstance(error_event.error, ValueError)
    assert str(error_event.error) == "Test error"
    assert error_event.error_context is not None
    assert "duration_ms" in error_event.error_context


def test_multiple_processors():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor1 = InMemoryProcessor()
    processor2 = InMemoryProcessor()
    telemetry.add_processor(processor1)
    telemetry.add_processor(processor2)

    @telemetry.track_call()
    def test_func(x: int) -> int:
        return x * 2

    result = test_func(5)
    assert result == 10

    events1 = processor1.get_events()
    events2 = processor2.get_events()
    assert len(events1) == 2
    assert len(events2) == 2
    for e1, e2 in zip(events1, events2):
        assert e1.event_type == e2.event_type
        assert e1.method_name == e2.method_name
        assert e1.args == e2.args
        assert e1.kwargs == e2.kwargs
        assert e1.response == e2.response
        assert e1.error == e2.error
        assert e1.error_context == e2.error_context
        assert e1.duration_ms == e2.duration_ms
        assert e1.timestamp <= e2.timestamp


def test_function_tracking():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    @telemetry.track_call()
    def standalone_function(x: int) -> int:
        return x * 2

    result = standalone_function(5)
    assert result == 10

    events = processor.get_events()
    assert len(events) == 2
    assert events[0].method_name.endswith("standalone_function")
    assert events[1].method_name.endswith("standalone_function")


def test_instance_method_tracking():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    class TestClass:
        @telemetry.track_call()
        def instance_method(self, x: int) -> int:
            return x * 2

    obj = TestClass()
    result = obj.instance_method(5)
    assert result == 10

    events = processor.get_events()
    assert len(events) == 2
    assert events[0].method_name.endswith("TestClass.instance_method")
    assert events[1].method_name.endswith("TestClass.instance_method")


def test_class_method_tracking():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    class TestClass:
        @classmethod
        @telemetry.track_call()
        def class_method(cls, x: int) -> int:
            return x * 3

    result = TestClass.class_method(5)
    assert result == 15

    events = processor.get_events()
    assert len(events) == 2
    assert events[0].method_name.endswith("TestClass.class_method")
    assert events[1].method_name.endswith("TestClass.class_method")


def test_static_method_tracking():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    class TestClass:
        @staticmethod
        @telemetry.track_call()
        def static_method(x: int) -> int:
            return x * 4

    result = TestClass.static_method(5)
    assert result == 20

    events = processor.get_events()
    assert len(events) == 2
    assert events[0].method_name.endswith("TestClass.static_method")
    assert events[1].method_name.endswith("TestClass.static_method")


def test_nested_class_tracking():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    class Outer:
        class Inner:
            @telemetry.track_call()
            def nested_method(self, x: int) -> int:
                return x * 2

    result = Outer.Inner().nested_method(5)
    assert result == 10

    events = processor.get_events()
    assert len(events) == 2
    assert events[0].method_name.endswith("Outer.Inner.nested_method")
    assert events[1].method_name.endswith("Outer.Inner.nested_method")


def test_exclude_parameter():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    @telemetry.track_call(exclude={"password", "token"}, include_first_arg=True)
    def sensitive_function(username: str, password: str, token: str) -> str:
        return f"User: {username}"

    result = sensitive_function("test_user", "secret_password", "private_token")
    assert result == "User: test_user"

    events = processor.get_events()
    assert len(events) == 2
    
    # Check that excluded parameters are masked
    start_event = events[0]
    assert start_event.args[0] == "test_user"  # username is included
    assert start_event.args[1] == "masked"     # password is masked
    assert start_event.args[2] == "masked"     # token is masked

    end_event = events[1]
    assert end_event.args[0] == "test_user"
    assert end_event.args[1] == "masked"
    assert end_event.args[2] == "masked"


def test_exclude_kwargs():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    @telemetry.track_call(exclude={"password", "token"}, include_first_arg=True)
    def sensitive_function(username: str, **kwargs) -> str:
        return f"User: {username}"

    result = sensitive_function("test_user", password="secret_password", token="private_token", visible="ok")
    assert result == "User: test_user"

    events = processor.get_events()
    assert len(events) == 2
    
    # Check that excluded kwargs are masked but others aren't
    start_event = events[0]
    assert start_event.args[0] == "test_user"
    assert start_event.kwargs["password"] == "masked"
    assert start_event.kwargs["token"] == "masked"
    assert start_event.kwargs["visible"] == "ok"


def test_include_first_arg_function():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    @telemetry.track_call(include_first_arg=True)
    def test_func(first: str, second: str) -> str:
        return f"{first}-{second}"

    result = test_func("one", "two")
    assert result == "one-two"

    events = processor.get_events()
    assert len(events) == 2
    
    # Check that first argument is included
    assert events[0].args == ("one", "two")
    assert events[1].args == ("one", "two")


def test_include_first_arg_method():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    class TestClass:
        def __init__(self, name: str):
            self.name = name
            
        @telemetry.track_call(include_first_arg=True)
        def method_with_self(self, param: str) -> str:
            return f"{self.name}-{param}"

    obj = TestClass("test")
    result = obj.method_with_self("param")
    assert result == "test-param"

    events = processor.get_events()
    assert len(events) == 2
    
    # Check that self is included as first argument
    assert len(events[0].args) == 2
    assert events[0].args[1] == "param"  # Second arg should be param
    # Can't directly check self, but we can check it's not removed


def test_default_exclude_self_method():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    class TestClass:
        def __init__(self, name: str):
            self.name = name
            
        @telemetry.track_call()  # Default include_first_arg=False
        def method_with_self(self, param: str) -> str:
            return f"{self.name}-{param}"

    obj = TestClass("test")
    result = obj.method_with_self("param")
    assert result == "test-param"

    events = processor.get_events()
    assert len(events) == 2
    
    # Check that self is excluded
    assert events[0].args == ("param",)
    assert events[1].args == ("param",)


def test_combined_exclude_and_include_first_arg():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    class User:
        @telemetry.track_call(exclude={"password"}, include_first_arg=True)
        def authenticate(self, username: str, password: str) -> bool:
            return username == "valid" and password == "correct"

    user = User()
    result = user.authenticate("valid", "correct")
    assert result is True

    events = processor.get_events()
    assert len(events) == 2
    
    # First arg (self) should be included, password should be masked
    assert len(events[0].args) == 3
    assert events[0].args[1] == "valid"     # username is included
    assert events[0].args[2] == "masked"    # password is masked
    
    assert len(events[1].args) == 3
    assert events[1].args[1] == "valid"
    assert events[1].args[2] == "masked"


def test_static_method_with_include_first_arg():
    settings = TelemetrySettings(enabled=True)
    telemetry = Telemetry(settings)
    processor = InMemoryProcessor()
    telemetry.add_processor(processor)

    class TestClass:
        @staticmethod
        @telemetry.track_call(include_first_arg=True)
        def static_method(first: str, second: str) -> str:
            return f"{first}-{second}"

    result = TestClass.static_method("one", "two")
    assert result == "one-two"

    events = processor.get_events()
    assert len(events) == 2
    
    # Check that all arguments are included
    assert events[0].args == ("one", "two")
    assert events[1].args == ("one", "two")
