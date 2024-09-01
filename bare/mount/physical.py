import platform

from .base import MountBase
from ..utils import execute_command


class MountDriveLinux(MountBase):
    """
    Handles mounting and unmounting of drives on Linux systems.
    Leverages `udisksctl` for performing the mount and unmount operations.
    """

    def mount(self, device_name):
        """
        Mounts a device by its name using `udisksctl`.

        Args:
            device_name (str): The device name to be mounted (e.g., 'sda1').

        Raises:
            Exception: If the `execute_command` function encounters an error.
        """
        try:
            command = f"udisksctl mount -b /dev/{device_name}"
            execute_command(command)
        except Exception as e:
            raise Exception(f"Failed to mount /dev/{device_name}: {e}")

    def unmount(self, path):
        """
        Unmounts a device by its mount path using `udisksctl`.

        Args:
            path (str): The mount path of the device to be unmounted.

        Raises:
            Exception: If the device is busy or if any other error occurs during the unmount operation.
        """
        try:
            command = f"udisksctl unmount -p {path}"
            execute_command(command)
        except Exception as e:
            msg = e.stderr.decode("utf-8").rstrip()
            if "busy" in msg:
                print(f"The device at {path} is being used and cannot be unmounted:")
                print(msg)
                print("Please close any applications that might be using the device.")
            else:
                raise Exception(f"Failed to unmount {path}: {msg}")


class MountDriveDarwin(MountBase):
    """
    Facilitates mounting and unmounting of drives on Darwin-based systems (macOS).
    Uses the `diskutil` command-line utility for mounting operations.
    """

    def mount(self, device_name):
        """
        Mounts a device by its name to a temporary directory created for this purpose.

        Args:
            device_name (str): The device name to be mounted (e.g., 'disk2').

        Raises:
            Exception: If an error occurs during the execution of the mount command.
        """
        try:
            path = self.generate_temporary_directory()
            cmd = f"diskutil mount -mountPoint {path} /dev/{device_name}"
            execute_command(cmd)
        except Exception as e:
            raise Exception(f"Failed to mount /dev/{device_name}: {e}")

    def unmount(self, path):
        """
        Unmounts a device from a specified path.

        Args:
            path (str): The path from which the device will be unmounted.

        Raises:
            Exception: If an error occurs during the execution of the unmount command.
        """
        try:
            cmd = f"diskutil unmount {path}"
            execute_command(cmd)
        except Exception as e:
            raise Exception(f"Failed to unmount {path}: {e}")


class MountDriveWin(MountBase):
    # TODO:
    def mount(self, device_name):
        path = self.generate_temporary_directory()
        # Create a diskpart script to assign a drive letter
        # script = f"select volume {volume}\nassign letter={drive_letter}"
        # process = subprocess.run(['diskpart'], input=script.encode(), check=True)
        # execute_command(cmd)

    def unmount(self, device_name):
        path = self.generate_temporary_directory()
        # Create a diskpart script to assign a drive letter
        # script = f"select volume {volume}\nassign letter={drive_letter}"
        # process = subprocess.run(['diskpart'], input=script.encode(), check=True)
        # execute_command(cmd)


class MountDrivePhysical(MountBase):
    """
    Facilitates the mounting and unmounting of physical drives. Supports operations
    across different operating systems by delegating to the appropriate subclass based
    on the runtime OS.
    """

    def mount(self, name=None, device=None):
        """
        Mounts a physical drive identified by its name or device dictionary. Automatically
        selects the correct mounting mechanism based on the operating system.

        Args:
            name (str, optional): The name of the drive to mount.
            device (dict, optional): The device dictionary containing details of the drive.

        Raises:
            Exception: If neither the device dictionary nor the drive name is provided.
            NotImplementedError: If the mounting functionality is not implemented for the OS.
        """
        if device is None and name is None:
            raise Exception("You should pass the device dict or the drive name")

        device = device or self.finder.find_device(name=name)

        if not device["mountpoints"]:
            mounter = self._get_mounter()
            mounter.mount(device["name"])
            return True
        else:
            print(f"Device is already mounted at: {device['mountpoints']}")
            return False

    def unmount(self, name=None, device=None, path=None):
        """
        Unmounts a physical drive identified by its name, device dictionary, or path. Automatically
        selects the correct unmounting mechanism based on the operating system.

        Args:
            name (str, optional): The name of the drive to unmount.
            device (dict, optional): The device dictionary containing details of the drive.
            path (str, optional): The path where the drive is mounted.

        Raises:
            Exception: If none of the identifying parameters are provided.
            NotImplementedError: If the unmounting functionality is not implemented for the OS.
        """
        if device is None and name is None and path is None:
            raise Exception(
                "You should pass the device dict, the drive name, or the path"
            )

        if path is None:
            device = device or self.finder.find_device(name=name)
            path = device["mountpoints"][0] if device["mountpoints"] else None

        if path:
            mounter = self._get_mounter()
            mounter.unmount(path)
            self.clean_device_temporary_directory(device=device, path=path)
        else:
            print("Device is already unmounted or no mount point found.")

    def _get_mounter(self):
        """
        Determines the appropriate mounter subclass based on the current operating system.

        Returns:
            An instance of the appropriate mounter subclass.

        Raises:
            NotImplementedError: If the mounting or unmounting functionality is not implemented for the OS.
        """
        os_type = platform.system()
        if os_type == "Linux":
            return MountDriveLinux()
        elif os_type == "Darwin":
            return MountDriveDarwin()
        elif os_type == "Windows":
            # Placeholder for future implementation
            # return MountDriveWin()
            raise NotImplementedError("Mounting in Windows is not implemented yet")
        else:
            raise NotImplementedError(f"Mounting in {os_type} is not implemented yet")
