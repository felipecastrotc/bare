import logging
import os
import platform

from ..bare.gocryptfs import Gocryptfs
from ..utils import execute_command
from .base import MountBase

logger = logging.getLogger(__name__)


class MountGocryptfs(MountBase):
    """
    Facilitates the mounting and unmounting of remote filesystems managed by rclone.
    Supports operations on Linux and Darwin operating systems.
    """

    def __init__(
        self,
        path,
        gocryptfs_password,
        gocryptfs_folder="",
    ):
        self.gofs = Gocryptfs(path, gocryptfs_password, gocryptfs_folder)

    def mount(self, label, device=None):
        """
        Mounts a gocryptfs-encrypted directory if it is not already mounted.

        Args:
            label: The label or path of the gocryptfs directory to mount.
            device: Optional. Reserved for compatibility; not currently used in logic.

        Returns:
            True if the directory was successfully mounted.
            False if it was already mounted or if mounting failed.
        """
        source = label
        device = self.finder.find_device(source)

        if len(device) > 0:
            logger.info(f"Device is already mounted at: {device['mountpoints']}")
            return False

        try:
            # Check if the folder is a valid gocryptfs repo; will raise if not
            cmd = "gocryptfs -info {}"
            execute_command(cmd.format(source), env=self.env)

            # Create a temporary directory to use as the mount point
            dest = self.generate_temporary_directory()
            assert os.path.exists(dest), (
                "Temporary folder for gocryptfs does not exist after creation."
            )

            # Set the path and mount the encrypted filesystem
            self.gofs.path = source
            self.gofs.mount(dest)
            return True

        except Exception as e:
            logger.info(
                f"The path: {source} is not a valid gocryptfs repository. Error: {e}"
            )
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
                logger.info("The rclone drive is already unmounted!!")
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
