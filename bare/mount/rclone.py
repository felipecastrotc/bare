import platform
import os

from .base import MountBase
from ..utils import execute_command


class MountDriveRclone(MountBase):
    """
    Facilitates the mounting and unmounting of remote filesystems managed by rclone.
    Supports operations on Linux and Darwin operating systems.
    """

    def mount(self, label=None, device=None):
        """
        Mounts a remote filesystem identified by a label or device dictionary to a temporary directory.

        Args:
            label (str, optional): The label of the remote filesystem to mount.
            device (dict, optional): The device dictionary containing details of the filesystem.

        Raises:
            Exception: If neither the device dictionary nor the label is provided.
            AssertionError: If creating a temporary directory fails.
        """
        if device is None and label is None:
            raise Exception("You should pass the device dict or the label")

        device = device or self.finder.find_device(label=label)

        if not device["mountpoints"]:
            path = self.generate_temporary_directory()
            assert os.path.exists(
                path
            ), "Failed to create a temporary folder for rclone mount"

            execute_command(f"rclone mount {device['label']} {path} --daemon")
            return True
        else:
            print(f"Device is already mounted at: {device['mountpoints']}")
            return False

    def unmount(self, label=None, device=None, path=None):
        """
        Unmounts a remote filesystem identified by a label, device dictionary, or mount path.

        Args:
            label (str, optional): The label of the remote filesystem to unmount.
            device (dict, optional): The device dictionary containing details of the filesystem.
            path (str, optional): The path where the filesystem is mounted.

        Raises:
            Exception: If none of the identifying parameters are provided.
            NotImplementedError: If the functionality is not implemented for the current OS.
        """
        if device is None and label is None and path is None:
            raise Exception(
                "You should pass the device dict, the label, or the path of the mounting point"
            )

        # Determine the unmount path
        if path is None:
            device = device or self.finder.find_device(label=label)
            if device["mountpoints"]:
                unmount_path = device["mountpoints"][0]
            else:
                print("The rclone drive is already unmounted!!")
                return None
        else:
            unmount_path = path

        # Check OS compatibility
        os_type = platform.system()
        if os_type in ["Linux", "Darwin"]:
            execute_command(f"umount {unmount_path}")
            self.clean_device_temporary_directory(device=device, path=unmount_path)
        else:
            raise NotImplementedError(
                "Unmounting rclone drives is not implemented for Windows yet!"
            )
