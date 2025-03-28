from importlib.metadata import PackageNotFoundError, version

from askui.logger import logger


PKG_NAME = "askui"


def get_pkg_version() -> str:
    try:
        return version(PKG_NAME)
    except PackageNotFoundError:
        logger.debug(f"Package \"{PKG_NAME}\" not found. Was the package renamed? Setting version to \"unknown\".s")
        return "unknown"
