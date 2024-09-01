import platform
import os

from .base import MountBase
from ..utils import execute_command, setup_environment
from ..bare.gocryptfs import Gocryptfs


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
        source = label
        device = self.finder.find_device(source)

        if len(device) > 0:
            print(f"Device is already mounted at: {device['mountpoints']}")
            return False
        else:
            try:
                # Check if a folder is a gocryptfs repo, if not it will raise an error
                cmd = "gocryptfs -info {}"
                out = execute_command(cmd.format(source), env=self.env)
                # Generate a temporary folder to mount the gocryptfs
                dest = self.generate_temporary_directory()
                assert os.path.exists(
                    dest
                ), "Failed to create a temporary folder for gocryptfs"
                # Build the gocryptfs
                self.gofs.path = source
                self.gofs.mount(dest)
                return True
            except:
                print(f"The path: {source} is not a valid gocryptfs repository.")
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
