from __future__ import annotations

import logging
import os
from typing import Any

from ..destination_handler import DestinationHandler
from .base import Base
from .restic import Restic
from .rsync import Rsync

logger = logging.getLogger(__name__)


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
        source: str,
        destination: str | None = None,
        vol_label: str | None = None,
        restic_password: str | None = None,
        hostname: str | None = None,
        name: str | None = None,
        storage: DestinationHandler | None = None,
    ) -> None:
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
        if storage is not None:
            self.storage = storage
        elif vol_label:
            self.storage = DestinationHandler(vol_label)
        elif destination:
            self.storage = DestinationHandler(destination)
        else:
            raise ValueError("Either 'destination' or 'vol_label' must be provided.")

        self.source = source
        self.destination = destination or ""
        self.restic_password = restic_password

    def perform_backup(
        self,
        use_restic: bool = False,
        use_rsync: bool = False,
        restic_args: dict[str, Any] | None = None,
        rsync_args: dict[str, Any] | None = None,
        mask: str | None = None,
        dry_run: bool = False,
    ) -> None:
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

    def _perform_restic_backup(
        self,
        base_dest_path: str,
        restic_args: dict[str, Any],
        mask: str | None,
        dry_run: bool,
    ) -> None:
        """Helper method to encapsulate Restic backup logic."""
        restic_runner = Restic(
            os.path.join(base_dest_path, self.destination),
            self.restic_password,
            hostname=self.hostname,
            name=self.name,
            check_hostname=False,
        )
        logger.info("Performing Restic backup...")
        restic_runner.backup(self.source, restic_args, mask, dry_run)

    def _perform_rsync_backup(
        self,
        base_dest_path: str,
        rsync_args: dict[str, Any],
        mask: str | None,
        dry_run: bool,
    ) -> None:
        """Helper method to encapsulate Rsync backup logic."""
        rsync_runner = Rsync(
            os.path.join(base_dest_path, self.destination),
            hostname=self.hostname,
            name=self.name,
            check_hostname=False,
        )
        logger.info("Performing Rsync backup...")
        rsync_runner.backup(self.source, rsync_args, mask, dry_run)
