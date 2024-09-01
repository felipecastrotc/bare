import os
from .base import Base
from ..utils import execute_command, dict2args, execute_command_test


class Rsync(Base):
    def __init__(
        self,
        path,
        rsync_folder="rsync",
        file_options="axHAX",
        hostname=None,
        name=None,
        check_hostname=False,
    ):
        super().__init__(hostname, name, check_hostname)
        # Location of the folder to receive the backup
        self.dest = os.path.join(path, hostname, rsync_folder)
        # Setup the base rsync command. the first {} is for the optional args
        # and the second for the source path
        self.base_cmd = f"rsync -{file_options} --info=progress2 --numeric-ids"
        self.base_cmd = self.base_cmd + " {} {} " + self.dest

    def run(self, source_path, args={}, mask=None, dry_run=False):
        print("Context: {}".format(self.name))
        cmd = self.base_cmd.format(dict2args(args), source_path)
        if dry_run:
            cmd += " --dry-run"
        return execute_command_test(cmd, None, mask)

    def backup(
        self, source, args={}, delete=True, ignore_error=True, mask=None, dry_run=False
    ):
        if delete:
            args["delete"] = ""
        if ignore_error:
            args["ignore-errors"] = ""
        self.run(source, args, mask, dry_run)
