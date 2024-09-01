import os
from .restic import Restic
from .rsync import Rsync
from ..destination_handler import DestinationHandler
from .base import Base


class Backup(Base):
    """
    Handles backup operations using Restic and Rsync, leveraging a MountManager for mounting operations.

    Inherits:
        Base: A base class providing common functionality for backup operations.

    Attributes:
        restic_password (str): Password for Restic backup encryption.
        rsync_password (str): Password for Rsync backup, if encrypted (not currently used).
        backup_path (str): Path to the directory to be backed up.
        mount_manager (MountManager): Instance for managing multiple mount operations.
    """

    def __init__(
        self,
        source,
        destination=None,
        vol_label=None,
        restic_password=None,
        hostname=None,
        name=None,
    ):
        """
        Initializes the backup with necessary parameters.

        Parameters:
            source (str): Source directory for backup.
            destination (str, optional): Destination directory for backup. Required if vol_label is not provided.
            vol_label (str, optional): Volume label if backing up to a specific volume.
            restic_password (str, optional): Password for Restic backup encryption.
            hostname (str, optional): Hostname for identifying the backup origin.
            name (str, optional): Name to identify the backup set.
        """
        super().__init__(hostname, name, True)
        if vol_label:
            self.storage = DestinationHandler(vol_label=vol_label)
        elif destination:
            self.storage = DestinationHandler(abs_path=destination)
        else:
            raise ValueError("Either 'destination' or 'vol_label' must be provided.")

        self.source = source
        self.destination = destination or ""
        self.restic_password = restic_password

    def perform_backup(
        self,
        use_restic=False,
        use_rsync=False,
        restic_args=None,
        rsync_args=None,
        mask=None,
        dry_run=False,
    ):
        """
        Performs the backup operation using specified methods: Restic or Rsync.

        Parameters:
            use_restic (bool): If True, use Restic for the backup.
            use_rsync (bool): If True, use Rsync for the backup.
            restic_args (dict, optional): Additional arguments for Restic backup.
            rsync_args (dict, optional): Additional arguments for Rsync backup.
            mask (str, optional): File mask to filter files for backup.
            dry_run (bool): If True, perform a trial run with no changes made.
        """
        restic_args = restic_args or {}
        rsync_args = rsync_args or {}

        with self.storage as base_dest_path:
            if use_restic:
                self._perform_restic_backup(base_dest_path, restic_args, mask, dry_run)
            if use_rsync:
                self._perform_rsync_backup(base_dest_path, rsync_args, mask, dry_run)

    def _perform_restic_backup(self, base_dest_path, restic_args, mask, dry_run):
        """Helper method to encapsulate Restic backup logic."""
        restic_runner = Restic(
            os.path.join(base_dest_path, self.destination),
            self.restic_password,
            hostname=self.hostname,
            name=self.name,
            check_hostname=False,
        )
        print("Performing Restic backup...")
        restic_runner.backup(self.source, restic_args, mask, dry_run)

    def _perform_rsync_backup(self, base_dest_path, rsync_args, mask, dry_run):
        """Helper method to encapsulate Rsync backup logic."""
        rsync_runner = Rsync(
            os.path.join(base_dest_path, self.destination),
            hostname=self.hostname,
            name=self.name,
            check_hostname=False,
        )
        print("Performing Rsync backup...")
        rsync_runner.backup(self.source, rsync_args, mask, dry_run)
