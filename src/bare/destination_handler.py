import os
from urllib.parse import urlparse
from .mount.drive import MountDrive
from .finder.devices import DeviceFinder


class DestinationHandler:
    def __init__(self, destination, relative_path=None, crypt=None):
        """
        Initialize a DestinationHandler object to manage different types of storage locations.

        Args:
        destination (str): The destination path or URL (e.g., volume label, absolute path, or Restic REST URL).
        relative_path (str): Relative path from the mount point (only applicable for volumes).
        crypt (str): Cryptographic option if needed.
        """
        self.destination = destination
        self.relative_path = relative_path
        self.crypt = crypt
        self.mounter = MountDrive()
        self.do_i_mounted = False
        self.destination_type = self.detect_destination_type()

    def detect_destination_type(self):
        """
        Detects the type of destination based on the provided destination.

        Returns:
        str: The type of destination ('volume', 'abs_path', or 'restic_rest_server').
        """
        # Check if it's a Restic REST server URL
        if self.destination.startswith("rest:"):
            parsed_url = urlparse(self.destination[5:])  # Strip 'rest:' and parse URL
            if parsed_url.scheme in ["http", "https"]:
                return "restic_rest_server"

        # Check if it's a volume label
        if not os.path.isabs(self.destination) and not os.path.exists(self.destination):
            return "volume"

        # Otherwise, assume it's an absolute path
        return "abs_path"

    def mount(self):
        """
        Mounts the drive, checks the absolute path, or handles Restic REST server as appropriate.

        Returns:
        str: The path or URL to be used after handling the destination.

        Raises:
        FileExistsError: If the absolute path does not exist and is specified.
        """
        if self.destination_type == "volume":
            return self._mount_drive()
        elif self.destination_type == "abs_path":
            return self._check_abs_path()
        elif self.destination_type == "restic_rest_server":
            return self._handle_restic_rest_server()

    def _mount_drive(self):
        """
        Helper method to mount the drive and return the mounted path.

        Returns:
            str: The mounted path combined with the relative path.

        Raises:
            RuntimeError: If no mount points are found for the volume label.
        """
        self.do_i_mounted = self.mounter.mount(self.destination)
        mount_points = self.mounter.get_mountpoint(self.destination)
        if not mount_points:
            raise RuntimeError(
                f"No mount points found for volume label: {self.destination}"
            )
        return os.path.join(
            mount_points[0], self.relative_path if self.relative_path else ""
        )

    def _check_abs_path(self):
        """
        Helper method to check if the absolute path exists.

        Returns:
            str: The absolute path if it exists.

        Raises:
            FileExistsError: If the absolute path does not exist.
        """
        if os.path.exists(self.destination):
            return self.destination
        else:
            raise FileExistsError(f"The path {self.destination} must exist.")

    def _handle_restic_rest_server(self):
        """
        Handles the Restic REST server destination.

        Returns:
            str: The Restic REST server URL.
        """
        return self.destination

    def unmount(self):
        """
        Unmounts the drive if it was mounted.
        """
        if self.destination_type == "volume" and self.do_i_mounted:
            self.mounter.unmount(self.destination)

    def __enter__(self):
        """
        Support for context manager entry. Attempts to mount the drive if necessary.
        """
        return self.mount()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Support for context manager exit. Cleans up by unmounting if necessary.
        """
        self.unmount()
