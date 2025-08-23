import platform
import os

from .finder.devices import DeviceFinder
from .mount.base import MountBase
from .mount.drive import MountDrive
from .utils import execute_command


class MountPointFinder:
    def find_device(self, mount_point):
        """Determine the method to use based on the operating system."""
        os_type = platform.system()
        if os_type == "Linux" or os_type == "Unix":
            return self._find_device_unix(mount_point)
        elif os_type == "Darwin":
            return self._find_device_darwin(mount_point)
        elif os_type == "Windows":
            return self._find_device_windows(mount_point)
        else:
            raise NotImplementedError(f"OS {os_type} not supported.")

    def _find_device_unix(self, mount_point):
        """Find the device mounted at `mount_point` for Unix/Linux."""
        with open("/proc/mounts", "r") as mounts:
            for line in mounts:
                parts = line.split()
                if parts[1] == mount_point:
                    # return parts[0], parts[2]
                    return parts[0].split("/dev/")[1]
        return None

    def _find_device_darwin(self, mount_point):
        """Find the device mounted at `mount_point` on macOS."""
        # TODO
        out = execute_command("mount")

        for line in out.splitlines():
            if mount_point in line:
                parts = line.split()
                # The device is typically the first part
                return parts[0].split("/dev/")[1]
        return None

    def _find_device_windows(self, mount_point):
        """Find the volume of the drive with the given letter on Windows."""
        # Adjust `mount_point` to match the expected input format for Windows (e.g., "C:")
        if not mount_point.endswith(":"):
            mount_point += ":"
        command = (
            f'wmic logicaldisk where DeviceID="{mount_point}" get VolumeName, DeviceID'
        )
        out = execute_command(command)
        # Parse the output to extract the device information
        if out:
            lines = out.strip().split("\n")
            if len(lines) > 1:  # Skip the header row
                return lines[1].strip()  # Return the first result
        return None


class MountManager:
    """
    Manages mounting and unmounting of devices, as well as cleaning up mount points and directories.
    Utilizes device finding and mount point management functionalities.
    """

    def __init__(self):
        self.finder = DeviceFinder()
        self.mount_base = MountBase()
        self.mounter = MountDrive()
        self.mount_finder = MountPointFinder()

    def get_mounted_devices(self):
        """
        Retrieves a dictionary of currently mounted devices and their mount points.

        Returns:
            dict: A dictionary with device identifiers as keys and mount paths as values.
        """
        dirname = self.mount_base.get_dirname()
        ls = os.listdir(dirname)
        my_files = [x for x in ls if self.mount_base.prefix in x]

        devices = {}
        for file in my_files:
            path = os.path.join(dirname, file)
            if os.path.ismount(path):
                device = self.mount_finder.find_device(path)
                devices[device] = path

        return devices

    def umount_all(self):
        """
        Unmounts all mounted devices that were mounted through this manager.
        Raises an exception if a device cannot be found.
        """
        mounted_devices = self.get_mounted_devices()
        all_devices = self.finder.find_device()

        for _, path in mounted_devices.items():
            self.mounter.unmount(path=path)

    def clean(self):
        """
        Cleans up all temporary directories and broken symbolic links created by the mount operations.
        """
        dirname = self.mount_base.get_dirname()
        my_files = self.get_folders_created()

        for file in my_files:
            path = os.path.join(dirname, file)
            if os.path.islink(path):
                self.clean_broken_symbolic_link(path)
            elif not os.path.ismount(path) and not os.listdir(path):
                os.rmdir(path)

    def get_folders_created(self):
        """
        Retrieves a list of folder names created by the mount operations.

        Returns:
            list: A list of folder names.
        """
        dirname = self.mount_base.get_dirname()
        ls = os.listdir(dirname)
        return [x for x in ls if self.mount_base.prefix in x]

    def clean_broken_symbolic_link(self, path):
        """
        Cleans up a broken symbolic link.

        Args:
            path (str): The path to the symbolic link.
        """
        target_path = os.readlink(path)
        absolute_target_path = os.path.join(os.path.dirname(path), target_path)
        if not os.path.exists(absolute_target_path):
            os.unlink(path)
