import os
from .base import Base
from ..utils import execute_command, dict2args, execute_command_test


class Gocryptfs(Base):
    def __init__(
        self,
        path,
        gocryptfs_password,
        gocryptfs_folder="",
    ):
        super().__init__(None, None, False)
        # Restic password -> TODO: better way to store the password
        self.env["GOCRYPTFS_PASSWORD"] = gocryptfs_password
        # Location of the restic repository
        self.path = path
        self.gocryptfs_folder = gocryptfs_folder
        # Setup the base directory used to access the repository
        self.cmd = 'gocryptfs -extpass "echo $GOCRYPTFS_PASSWORD" {} {} {}'

    def run(self, cmd="", args={}, mask=None):
        cmd = self.cmd.format(dict2args(args, double="-"), self.path, cmd)
        # return execute_command_test(cmd, self.env, mask)
        return execute_command(cmd, self.env, mask)

    def init(self):
        self.run({"init": ""})

    def mount(self, destination, args={}, mask=None):
        self.run(destination, args, mask)

    def __getattr__(self, name):
        # This method is called when an undefined attribute/method is accessed
        def method(**kwargs):
            # Redirect the call to the 'run' method with the method name as the command
            return self.run(name, args=kwargs)

        return method
