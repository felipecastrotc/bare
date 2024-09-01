from .base import MountBase
from .physical import MountDrivePhysical
from .rclone import MountDriveRclone


class MountDrive(MountBase):
    """
    Provides functionality to mount and unmount drives, automatically selecting
    the appropriate mounting strategy based on the drive's file system type.
    """

    def mount(self, label=None, device_name=None):
        """
        Mounts a device identified by its label or name. Automatically selects
        the correct mounting strategy (rclone or physical) based on the file system type.

        Args:
            label (str, optional): The label of the device to mount.
            device_name (str, optional): The name of the device to mount.

        Raises:
            Exception: If the device cannot be found or an unsupported file system type is encountered.
        """
        device = self.get_device(label=label, device_name=device_name)

        if device is None:
            raise Exception("Device not found.")

        if device["fstype"] == "fuse.rclone":
            mounter = MountDriveRclone()
        else:
            mounter = MountDrivePhysical()

        return mounter.mount(device=device)

    #    def unmount(self, label=None, device_name=None, path=None):
    #         if path is not None:
    #             device = None
    #         else:
    #             device = self.get_device(label, device_name)
    #         if device["fstype"] == "fuse.rclone":
    #             mount = MountDriveRclone()
    #         else:
    #             mount = MountDrivePhysical()
    #         mount.unmount(name=device_name, device=device, path=path)

    def unmount(self, label=None, device_name=None, path=None):
        """
        Unmounts a device identified by its label, name, or mount path. Automatically selects
        the correct unmounting strategy (rclone or physical) based on the file system type.

        Args:
            label (str, optional): The label of the device to unmount.
            device_name (str, optional): The name of the device to unmount.
            path (str, optional): The mount path of the device to unmount.

        Raises:
            Exception: If the device cannot be found (when path is not provided) or an unsupported file system type is encountered.
        """

        device = self.get_device(label=label, device_name=device_name, path=path)

        if len(device) < 1:
            raise Exception("Device not found.")

        if device["fstype"] == "fuse.rclone":
            mounter = MountDriveRclone()
        else:
            mounter = MountDrivePhysical()

        mounter.unmount(device=device, path=path)

    def get_mountpoint(self, label=None, device_name=None):
        """
        Retrieves the mount points for a device identified by its label or name.

        Args:
            label (str, optional): The label of the device.
            device_name (str, optional): The name of the device.

        Returns:
            list: A list of mount points for the device.

        Raises:
            Exception: If the device cannot be found.
        """
        device = self.get_device(label=label, device_name=device_name)
        if device is None:
            raise Exception("Device not found.")
        return device["mountpoints"]
