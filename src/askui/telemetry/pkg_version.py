import logging
from importlib.metadata import Distribution, PackageNotFoundError, distribution, version

logger = logging.getLogger(__name__)


def _get_module_name() -> str:
    """Return the top-level package name from the module path."""
    if __name__ == "__main__":
        error_msg = "This module is not meant to be run directly."
        raise RuntimeError(error_msg)

    parts = __name__.split(".")
    if not parts:
        error_msg = "Failed to determine the module name - empty module path"
        raise RuntimeError(error_msg)

    return parts[0]


def _get_distribution() -> Distribution | None:
    """Get the distribution for the current package safely."""
    try:
        module_name = _get_module_name()
        return distribution(module_name)
    except (PackageNotFoundError, RuntimeError) as e:
        logger.warning("Failed to get distribution", extra={"error": str(e)})
        return None


def get_pkg_version() -> str:
    """Return the package version or 'unknown' if version cannot be determined."""
    dist = _get_distribution()
    if dist is None:
        return "unknown"

    try:
        return version(dist.name)
    except PackageNotFoundError:
        logger.debug(
            'Package not found. Setting version to "unknown".',
            extra={"package_name": dist.name},
        )
        return "unknown"
