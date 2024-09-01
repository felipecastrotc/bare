import os
from .base import Base
from ..utils import execute_command, dict2args, execute_command_test


class Restic(Base):
    def __init__(
        self,
        path,
        restic_password,
        restic_folder="restic",
        hostname=None,
        name=None,
        check_hostname=True,
    ):
        super().__init__(hostname, name, check_hostname)
        # Restic password -> TODO: better way to store the password
        self.env["RESTIC_PASSWORD"] = restic_password
        # Location of the restic repository
        self.path = path
        self.restic_folder = restic_folder
        # Setup the base directory used to access the repository
        self.cmd = "restic {} {} {}"
        self.repo = f"-r {os.path.join(path, restic_folder)} -v"

    def run(self, cmd, args={}, mask=None, dry_run=False):
        print("Context: {}".format(self.name))
        cmd = self.cmd.format(self.repo, cmd, dict2args(args))
        if dry_run:
            cmd += " --dry-run"
        # return execute_command_test(cmd, self.env, mask)
        return execute_command(cmd, self.env, mask)

    def init(self):
        self.run("init")

    def backup(self, source, args={}, mask=None, dry_run=False):
        self.run(f"backup {source} -H {self.hostname}", args, mask, dry_run)

    def __getattr__(self, name):
        # This method is called when an undefined attribute/method is accessed
        def method(**kwargs):
            # Redirect the call to the 'run' method with the method name as the command
            return self.run(name, args=kwargs)

        return method
