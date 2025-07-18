from pathlib import Path

from askui.utils.api_utils import ListQuery, list_resource_paths


def _create_json_files(tmp_path: Path, names: list[str]) -> None:
    for name in names:
        (tmp_path / name).write_text("{}")


def _create_non_json_files(tmp_path: Path, names: list[str]) -> None:
    for name in names:
        (tmp_path / name).write_text("notjson")


def test_list_resource_paths_empty_dir(tmp_path: Path) -> None:
    result = list_resource_paths(tmp_path, ListQuery())
    assert result == []


def test_list_resource_paths_only_non_json(tmp_path: Path) -> None:
    _create_non_json_files(tmp_path, ["a.txt", "b.md"])
    result = list_resource_paths(tmp_path, ListQuery())
    assert result == []


def test_list_resource_paths_default(tmp_path: Path) -> None:
    files = ["b.json", "a.json", "c.json"]
    _create_json_files(tmp_path, files)
    result = list_resource_paths(tmp_path, ListQuery())
    assert [f.name for f in result] == sorted(files, reverse=True)


def test_list_resource_paths_asc(tmp_path: Path) -> None:
    files = ["b.json", "a.json", "c.json"]
    _create_json_files(tmp_path, files)
    result = list_resource_paths(tmp_path, ListQuery(order="asc"))
    assert [f.name for f in result] == sorted(files)


def test_list_resource_paths_after_not_found(tmp_path: Path) -> None:
    files = ["a.json", "b.json", "c.json"]
    _create_json_files(tmp_path, files)
    result = list_resource_paths(tmp_path, ListQuery(after="zzz.json", order="asc"))
    assert result == []


def test_list_resource_paths_before_not_found(tmp_path: Path) -> None:
    files = ["a.json", "b.json", "c.json"]
    _create_json_files(tmp_path, files)
    result = list_resource_paths(tmp_path, ListQuery(before="000.json", order="asc"))
    assert result == []


def test_list_resource_paths_after_greater_than_all(tmp_path: Path) -> None:
    files = ["a.json", "b.json", "c.json"]
    _create_json_files(tmp_path, files)
    result = list_resource_paths(tmp_path, ListQuery(after="d.json", order="asc"))
    assert result == []


def test_list_resource_paths_before_less_than_all(tmp_path: Path) -> None:
    files = ["a.json", "b.json", "c.json"]
    _create_json_files(tmp_path, files)
    result = list_resource_paths(tmp_path, ListQuery(before="0.json", order="asc"))
    assert result == []


def test_list_resource_paths_invalid_file_names(tmp_path: Path) -> None:
    files = ["a.json", "b.json", "c.json", "invalid[.json", "weird$.json"]
    _create_json_files(tmp_path, files)
    result = list_resource_paths(tmp_path, ListQuery(order="asc"))
    # Should include all valid .json files, even with odd names
    assert {f.name for f in result} == set(files)


def test_list_resource_paths_limit(tmp_path: Path) -> None:
    files = ["a.json", "b.json", "c.json"]
    _create_json_files(tmp_path, files)
    query = ListQuery(order="asc", limit=2)
    result = list_resource_paths(tmp_path, query)
    assert (
        len(result) == 3
    )  # list_resource_paths does not apply limit, just sorting/filtering
