import pathlib

import pytest


@pytest.fixture
def path_fixtures() -> pathlib.Path:
    """Fixture providing the path to the fixtures directory."""
    return pathlib.Path().absolute() / "tests" / "fixtures"

@pytest.fixture
def path_fixtures_images(path_fixtures: pathlib.Path) -> pathlib.Path:
    """Fixture providing the path to the images directory."""
    return path_fixtures / "images"

@pytest.fixture
def path_fixtures_github_com__icon(path_fixtures_images: pathlib.Path) -> pathlib.Path:
    """Fixture providing the path to the github com icon image."""
    return path_fixtures_images / "github_com__icon.png"
