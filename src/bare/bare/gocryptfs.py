from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..utils import dict2args, execute_command
from .base import Base


class Gocryptfs(Base):
    def __init__(
        self,
        path: str,
        gocryptfs_password: str,
        gocryptfs_folder: str = "",
    ) -> None:
        super().__init__(None, None, False)
        # Restic password -> TODO: better way to store the password
        self.env["GOCRYPTFS_PASSWORD"] = gocryptfs_password
        # Location of the restic repository
        self.path = path
        self.gocryptfs_folder = gocryptfs_folder
        # Setup the base directory used to access the repository
        self.cmd = 'gocryptfs -extpass "echo $GOCRYPTFS_PASSWORD" {} {} {}'

    def run(
        self,
        cmd: str = "",
        args: dict[str, Any] | None = None,
        mask: str | None = None,
    ) -> str:
        if args is None:
            args = {}
        cmd = self.cmd.format(dict2args(args, double="-"), self.path, cmd)
        # return execute_command_test(cmd, self.env, mask)
        return execute_command(cmd, self.env, mask)

    def init(self) -> None:
        self.run({"init": ""})

    def mount(
        self,
        destination: str,
        args: dict[str, Any] | None = None,
        mask: str | None = None,
    ) -> None:
        if args is None:
            args = {}
        self.run(destination, args, mask)

    def __getattr__(self, name: str) -> Callable[..., str]:
        # This method is called when an undefined attribute/method is accessed
        def method(**kwargs: Any) -> str:
            # Redirect the call to the 'run' method with the method name as the command
            return self.run(name, args=kwargs)

        return method
