"""Package initialization: exposes primary interfaces and utilities for backup operations.

This module aggregates key classes and utility functions used throughout
the backup system, including handlers for backup tools, mounting, and
destination management.
"""

# Main Backup Classes
from .bare.backup import Backup
from .bare.gocryptfs import Gocryptfs
from .bare.restic import Restic
from .bare.rsync import Rsync
from .destination_handler import DestinationHandler

# Support Classes
from .finder.devices import DeviceFinder
from .mount.drive import MountDrive
from .mount_manager import MountManager

# Utility Functions for Debugging & Execution
from .utils import execute_command, parse_mount

__all__ = [
    # Main backup classes
    "Backup",
    "Gocryptfs",
    "Restic",
    "Rsync",
    "DestinationHandler",
    # Support classes
    "DeviceFinder",
    "MountDrive",
    "MountManager",
    # Utility functions
    "execute_command",
    "parse_mount",
]
