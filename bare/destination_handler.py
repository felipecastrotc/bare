import os
from .mount.drive import MountDrive
from .finder.devices import DeviceFinder


class DestinationHandler:
    def __init__(self, vol_label=None, rel_path=None, abs_path=None, crypt=None):
        """
        Initialize a DestinationHandler object to manage different types of storage locations.

        Args:
        vol_label (str): Volume label of the drive if it needs to be mounted.
        rel_path (str): Relative path from the mount point.
        abs_path (str): Absolute path to a directory that does not need mounting.
        """
        self.vol_label = vol_label
        self.rel_path = rel_path
        self.abs_path = abs_path
        self.crypt = crypt
        self.mounter = MountDrive()
        # Variable to control if I mounted or not a device
        self.do_i_mounted = False

    def mount(self):
        """
        Mounts the drive specified by the volume label and returns the appropriate path.

        Returns:
        str: The path to be used after mounting.

        Raises:
        FileExistsError: If the absolute path does not exist and is specified.
        """
        if self.vol_label:
            path = self._mount_drive()
        elif self.abs_path:
            path = self._check_abs_path()
        # if self.crypt is not None:

    def _mount_drive(self):
        """
        Helper method to mount the drive and return the mounted path.

        Returns:
            str: The mounted path combined with the relative path.

        Raises:
            RuntimeError: If no mount points are found or there are multiple ambiguous mount points.
        """
        self.do_i_mounted = self.mounter.mount(self.vol_label)
        mount_points = self.mounter.get_mountpoint(self.volume_label)
        if not mount_points:
            raise RuntimeError(
                f"No mount points found for volume label: {self.volume_label}"
            )
        # For now I'm assuming the first mountpoint
        # if len(mount_points) > 1:
        #     raise RuntimeError(f"Multiple mount points found for volume label: {self.volume_label}, please specify which to use.")
        return os.path.join(
            mount_points[0], self.relative_path if self.relative_path else ""
        )

    def _check_abs_path(self):
        if os.path.exists(self.abs_path):
            return self.abs_path
        else:
            raise FileExistsError(f"The path {self.abs_path} must exist.")

    def unmount(self):
        """
        Unmounts the drive if it was mounted.
        """
        if self.vol_label:
            if self.i_mounted:
                self.mounter.unmount(self.vol_label)

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
