import os

import tempfile
import stat

from ..finder.devices import DeviceFinder


class MountBase:
    """
    Base class for managing mounting and unmounting devices, including creating,
    managing, and cleaning up temporary directories.
    """

    def __init__(self):
        self.finder = DeviceFinder()
        self.prefix = "BUP.tmp."

    def get_dirname(self):
        """
        Creates a temporary directory to extract its path and then removes it,
        effectively fetching a directory name for potential use.

        Returns:
            str: The path of the directory intended for temporary use.
        """
        temp_dir = self.generate_temporary_directory(symbolic=True)
        path = os.path.dirname(temp_dir)
        return path

    def generate_temporary_directory(self, symbolic=False):
        """
        Generates a temporary directory with restrictive permissions. If the directory
        is intended for symbolic link creation, it is removed after creation.

        Args:
            symbolic (bool): Determines if the directory is intended for symbolic link purposes.

        Returns:
            str: The path to the temporary directory.
        """
        temp_dir = tempfile.mkdtemp(prefix=self.prefix)
        os.chmod(
            temp_dir, stat.S_IRWXU
        )  # Secure the directory with restrictive permissions.
        if symbolic:
            os.rmdir(
                temp_dir
            )  # Remove the directory if it's for symbolic link purposes.
        return temp_dir

    def clean_device_temporary_directory(self, device=None, path=None):
        """
        Cleans up a temporary directory created by this instance, either specified by a device's
        mountpoint or a direct path.

        Args:
            device (dict, optional): Device information dictionary containing mountpoints.
            path (str, optional): Direct path of the temporary directory to be removed.

        Raises:
            ValueError: If neither device nor path is provided.
        """
        if device is None and path is None:
            raise ValueError("A device dictionary or a path must be provided.")
        if device:
            for mountpoint in device.get("mountpoints", []):
                if self.prefix in mountpoint and os.path.exists(mountpoint):
                    os.rmdir(mountpoint)
        if path and self.prefix in path and os.path.exists(path):
            os.rmdir(path)

    def get_device(self, label=None, device_name=None, path=None):
        """
        Retrieves a device based on its label or name or mountpoint. Exactly one parameter must be provided.

        Args:
            label (str, optional): The label of the device to find.
            device_name (str, optional): The name of the device to find.

        Returns:
            dict: The first device matching the given criteria.

        Raises:
            ValueError: If neither label nor device_name is provided, or if multiple devices match.
        """
        if label is None and device_name is None and path is None:
            raise ValueError(
                "Either a label or a device name or the mountpint must be provided."
            )

        devices = self.finder.find_device(label, device_name, path)

        if len(devices) == 0:
            raise ValueError(f"I could find the device with specified label: {label}.")

        if len(devices) > 1:
            raise ValueError("Multiple devices found with the specified label/name.")

        return devices[0]
