import logging
import os
import platform
from shutil import which

from ..utils import dict2args, execute_command
from .base import Base

logger = logging.getLogger(__name__)


class Restic(Base):
    def __init__(
        self,
        path,
        password,
        restic_folder="restic",
        hostname=None,
        name=None,
        check_hostname=True,
        runner="restic",
        bin_path=None,
    ):
        super().__init__(hostname, name, check_hostname)
        # Restic password -> TODO: better way to store the password
        self.env["RESTIC_PASSWORD"] = password
        # Location of the restic repository
        self.path = path
        self.restic_folder = restic_folder

        # Setup the runner restic/rustic
        self.runner = runner  # alternative "rustic"
        if bin_path is None:
            bin_restic = which("restic")
            bin_rustic = which("rustic")
        else:
            bin_restic, bin_rustic = bin_path, bin_path
        self.restic_cmd = bin_restic + " {} {} {}"
        self.rustic_cmd = bin_rustic + " {} {} {} --password " + password
        if self.runner == "restic":
            self.cmd = self.restic_cmd
        else:
            self.cmd = self.rustic_cmd

        # Setup the base directory used to access the repository
        if len(restic_folder) > 0:
            self.repo = f"-r {os.path.join(path, restic_folder)}"
        else:
            self.repo = f"-r {path}"

    def run(self, cmd, args=None, mask=None, dry_run=False, custom_runner=None):
        if args is None:
            args = {}
        logger.info(f"Context: {self.name}")
        # Select runner
        runner = self.cmd if custom_runner is None else custom_runner
        # Build command
        cmd = runner.format(self.repo, cmd, dict2args(args))
        if dry_run:
            cmd += " --dry-run"
        # return execute_command_test(cmd, self.env, mask)
        logger.info(cmd)
        return execute_command(cmd, self.env, mask, ignore_error=True)

    def init(self):
        self.run("init")

    def backup(self, source, args=None, mask=None, dry_run=False):
        if args is None:
            args = {}
        if self.hostname is not None:
            base_cmd = f"backup {source} --host {self.hostname} "
        else:
            base_cmd = f"backup {source} "
        # Rustic
        if self.runner == "rustic":
            self.run(base_cmd + f"--as-path {mask}", args, None, dry_run)
        else:
            # For MacOS we cannot use proot so it goes back to rustic
            if mask is not None and platform.system() == "Darwin":
                self.run(
                    base_cmd + f"--as-path {mask}",
                    args,
                    None,
                    dry_run,
                    custom_runner=self.rustic_cmd,
                )
            else:
                # Uses proot
                self.run(base_cmd, args, mask, dry_run)

    def forget(self, options, hostname_filter=True, dry_run=False):
        # Base command for forgetting and pruning backups
        base_cmd = "forget --prune "
        # Append the host filter to the command if the hostname is set
        if self.hostname is not None and hostname_filter:
            base_cmd += "--host " + self.hostname

        self.run(base_cmd, args=options, dry_run=dry_run)

    def check(self, options, dry_run=False):
        # Base command for forgetting and pruning backups
        base_cmd = "check "
        self.run(base_cmd, args=options, dry_run=dry_run)

    def mount(self, destination, args=None, mask=None, dry_run=False):
        # Currently rustic does not support the mount option.
        if args is None:
            args = {}
        self.run(
            f"mount {destination}", args, mask, dry_run, custom_runner=self.restic_cmd
        )

    def __getattr__(self, name):
        # This method is called when an undefined attribute/method is accessed
        def method(**kwargs):
            # Redirect the call to the 'run' method with the method name as the command
            return self.run(name, args=kwargs)

        return method
