import askui
from askui.telemetry.pkg_version import get_pkg_version


def test_version_consistency() -> None:
    package_version = get_pkg_version()
    module_version = askui.__version__
    assert package_version == module_version, (
        f"Version mismatch: package={package_version}, module={module_version}; "
        "Please run: pdm sync"
    )
