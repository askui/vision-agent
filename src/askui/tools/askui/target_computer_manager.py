from askui.tools.askui.target_computer import (
    RemoteTargetComputer,
    TargetComputer,
)


class TargetComputerManager:
    """
    Manages a collection of `TargetComputer` instances and tracks the currently
    active one.

    Constraints:
        - At most one local target computer (where `is_local` is `True`) may be
          registered at a time.
        - Session GUIDs are unique across registered targets.
        - Remote target addresses must be unique across registered remote targets.

    The first target added becomes the active one by default. Use `switch` to change
    the active target.

    Args:
        target_computers (list[TargetComputer] | None, optional): Initial targets
            to register.
    """

    def __init__(
        self,
        target_computers: list[TargetComputer] | None = None,
    ) -> None:
        self._targets: list[TargetComputer] = []
        self._active_session_guid: str | None = None
        if target_computers:
            for target in target_computers:
                self.add(target)

    def add(self, target: TargetComputer) -> TargetComputer:
        """
        Register a target computer.

        Args:
            target (TargetComputer): The target to register.

        Returns:
            TargetComputer: The registered target.

        Raises:
            ValueError: If a local target is already registered, the same session
                GUID is already registered, or a remote target with the same address
                is already registered.
        """
        if target.is_local and any(t.is_local for t in self._targets):
            error_msg = "Only one local target computer may be registered"
            raise ValueError(error_msg)
        if any(t.session_guid == target.session_guid for t in self._targets):
            error_msg = (
                f"Target computer with session GUID {target.session_guid} "
                "is already registered"
            )
            raise ValueError(error_msg)
        if not target.is_local and any(
            (not t.is_local) and t.address == target.address for t in self._targets
        ):
            error_msg = (
                f"Remote target computer with address {target.address!r} "
                "is already registered"
            )
            raise ValueError(error_msg)
        self._targets.append(target)
        if self._active_session_guid is None:
            self._active_session_guid = target.session_guid
        return target

    def add_remote(
        self,
        address: str,
        description: str,
    ) -> RemoteTargetComputer:
        """
        Convenience method to construct and register a remote target computer.

        Args:
            address (str): gRPC address of the remote controller.
            description (str): Human-readable description.

        Returns:
            RemoteTargetComputer: The newly registered target.
        """
        target = RemoteTargetComputer(address=address, description=description)
        self.add(target)
        return target

    def reset(self) -> None:
        """Remove all registered targets."""
        self._targets = []
        self._active_session_guid = None

    def remove(self, session_guid: str) -> None:
        """
        Remove a registered target by its session GUID.

        Args:
            session_guid (str): The session GUID of the target to remove.

        Raises:
            KeyError: If no target with the given session GUID is registered.
        """
        index = self._index_of(session_guid)
        del self._targets[index]
        if self._active_session_guid == session_guid:
            self._active_session_guid = (
                self._targets[0].session_guid if self._targets else None
            )

    def list(self) -> list[TargetComputer]:
        """Return a list of all registered targets."""
        return list(self._targets)

    def get(self, session_guid: str) -> TargetComputer:
        """
        Return the registered target with the given session GUID.

        Raises:
            KeyError: If no target with the given session GUID is registered.
        """
        return self._targets[self._index_of(session_guid)]

    def switch(self, session_guid: str) -> TargetComputer:
        """
        Set the active target by its session GUID.

        Args:
            session_guid (str): The session GUID of the target to activate.

        Returns:
            TargetComputer: The newly active target.

        Raises:
            KeyError: If no target with the given session GUID is registered.
        """
        target = self.get(session_guid)
        self._active_session_guid = session_guid
        return target

    @property
    def active(self) -> TargetComputer | None:
        """The currently active target, or `None` if no targets are registered."""
        if self._active_session_guid is None:
            return None
        return self.get(self._active_session_guid)

    def __len__(self) -> int:
        return len(self._targets)

    def _index_of(self, session_guid: str) -> int:
        for i, target in enumerate(self._targets):
            if target.session_guid == session_guid:
                return i
        error_msg = f"No target computer with session GUID {session_guid} is registered"
        raise KeyError(error_msg)


__all__ = ["TargetComputerManager"]
