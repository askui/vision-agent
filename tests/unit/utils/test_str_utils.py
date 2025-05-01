from askui.utils.str_utils import truncate_long_strings


def test_truncate_long_strings_with_dict() -> None:
    input_data = {"short": "short", "long": "a" * 101, "nested": {"long": "b" * 101}}
    expected = {
        "short": "short",
        "long": "a" * 20 + "... [shortened]",
        "nested": {"long": "b" * 20 + "... [shortened]"},
    }
    assert truncate_long_strings(input_data) == expected


def test_truncate_long_strings_with_list() -> None:
    input_data = ["short", "a" * 101, ["b" * 101]]
    expected = ["short", "a" * 20 + "... [shortened]", ["b" * 20 + "... [shortened]"]]
    assert truncate_long_strings(input_data) == expected


def test_truncate_long_strings_with_string() -> None:
    assert truncate_long_strings("short") == "short"
    assert truncate_long_strings("a" * 101) == "a" * 20 + "... [shortened]"


def test_truncate_long_strings_with_custom_params() -> None:
    input_data = "a" * 101
    expected = "a" * 10 + "... [custom]"
    assert (
        truncate_long_strings(
            input_data, max_length=50, truncate_length=10, tag="[custom]"
        )
        == expected
    )


def test_truncate_long_strings_with_mixed_data() -> None:
    input_data = {
        "list": ["short", "a" * 101],
        "dict": {"long": "b" * 101},
        "str": "c" * 101,
    }
    expected = {
        "list": ["short", "a" * 20 + "... [shortened]"],
        "dict": {"long": "b" * 20 + "... [shortened]"},
        "str": "c" * 20 + "... [shortened]",
    }
    assert truncate_long_strings(input_data) == expected


def test_truncate_long_strings_with_empty_data() -> None:
    assert truncate_long_strings({}) == {}
    assert truncate_long_strings([]) == []
    assert truncate_long_strings("") == ""
