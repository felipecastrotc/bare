import platform
import json
import plistlib

from ..utils import execute_command


class DriveFinderLinux:
    """
    Enables the discovery of physical drives and their partitions on Linux systems.
    It utilizes the `lsblk` command to retrieve drive information, parsing it to identify
    and return details about each physical drive and partition.
    """

    DEFAULT_LABEL = ""
    DEFAULT_MOUNTPOINTS = []

    def extract_partitions(self, blks):
        """
        Identifies and returns all partitions (leaf nodes) from the provided block device structure.

        Args:
            blks (list of dict): The block devices structure as returned by `lsblk -J`.

        Returns:
            list of dict: A list containing information about each identified partition.
        """
        partitions = []
        self._recurse_partitions(blks, partitions)
        return partitions

    def _recurse_partitions(self, nodes, partitions):
        """
        Recursively traverses the block device tree to find and append leaf nodes (partitions) to the partitions list.

        Args:
            nodes (list of dict): The current list of nodes (block devices or partitions) to process.
            partitions (list of dict): The list to which identified partitions are appended.
        """
        for node in nodes:
            if "children" in node:
                self._recurse_partitions(node["children"], partitions)
            else:
                partitions.append(node)

    def get_physical_drives(self):
        """
        Retrieves and processes information about physical drives and their partitions on Linux.

        Returns:
            list of dict: A list of dictionaries, each representing a partition with keys for name,
                          label, mountpoints, and fstype, with missing data filled in with defaults.
        """
        lsblk_command = "lsblk -o name,label,mountpoints,fstype -J"
        lsblk_output = execute_command(lsblk_command)
        blks = json.loads(lsblk_output)["blockdevices"]

        found_devices = self.extract_partitions(blks)

        # Apply default mountpoints where necessary
        for device in found_devices:
            if not device.get("mountpoints") or device["mountpoints"] == [None]:
                device["mountpoints"] = self.DEFAULT_MOUNTPOINTS

        return found_devices


class DriveFinderDarwin:
    """
    Facilitates the discovery of physical drives and their partitions on macOS.
    Utilizes the `diskutil` command to fetch drive information and parses it accordingly.
    """

    DEFAULT_LABEL = ""
    DEFAULT_MOUNTPOINTS = []
    DEFAULT_FSTYPE = ""

    FILESYSTEM_CONVERSION_MAP = {
        "Apple_APFS_ISC": "apfs_isc",
        "Apple_APFS_Recovery": "apfs_recovery",
        "Apple_APFS_Container": "apfs_container",
        "Apple_APFS": "apfs",
        "Windows_NTFS": "ntfs",
    }

    def get_physical_drives(self):
        """
        Executes a command to fetch information about physical drives and their partitions,
        parsing the output into a structured list of dictionaries.

        Each dictionary contains details about a drive or partition, including its identifier,
        volume label, mount points, and file system type, with conversions applied to standardize
        file system type names.

        Returns:
            list of dict: A list of dictionaries, each representing a physical drive or partition
                          with keys for name, label, mountpoints, and fstype.
        """
        diskutil_command = "diskutil list -plist"
        diskutil_output = execute_command(diskutil_command)
        disks_info = plistlib.loads(diskutil_output.encode("utf-8"))

        found_devices = []
        for disk in disks_info.get("AllDisksAndPartitions", []):
            device_info = self._parse_disk_info(disk)
            found_devices.append(device_info)

            # Process partitions if they exist
            for partition in disk.get("Partitions", []):
                partition_info = self._parse_partition_info(partition)
                found_devices.append(partition_info)

        return found_devices

    def _parse_disk_info(self, disk):
        """
        Parses disk information, applying defaults and converting filesystem types as necessary.

        Args:
            disk (dict): The disk information dictionary from `diskutil`.

        Returns:
            dict: A dictionary with processed disk information.
        """
        return {
            "name": disk.get("DeviceIdentifier"),
            "label": disk.get("VolumeName", self.DEFAULT_LABEL),
            "mountpoints": self._parse_mountpoint(disk),
            "fstype": self.FILESYSTEM_CONVERSION_MAP.get(
                disk.get("Content", ""), disk.get("Content", "")
            ),
        }

    def _parse_partition_info(self, partition):
        """
        Parses partition information, applying defaults and converting filesystem types as necessary.

        Args:
            partition (dict): The partition information dictionary.

        Returns:
            dict: A dictionary with processed partition information.
        """
        return {
            "name": partition.get("DeviceIdentifier"),
            "label": partition.get("VolumeName", "No Label"),
            "mountpoints": self._parse_mountpoint(partition),
            "fstype": self.FILESYSTEM_CONVERSION_MAP.get(
                partition.get("Content", ""), partition.get("Content", "")
            ),
        }

    def _parse_mountpoint(self, data):
        """
        Parses the mount point information from the given data, adjusting paths as necessary.

        Args:
            data (dict): A dictionary containing the mount point information.

        Returns:
            list or str: The processed mount point(s), adjusted if prefixed with '/private'.
        """
        path = data.get("MountPoint")
        if path:
            if platform.system() == "Darwin":
                prefix = "/private"
                if path.startswith(prefix):
                    return [path[len(prefix) :]]  # Slice off the prefix
                else:
                    return [path]  # Slice off the prefix
            else:
                return path  # Return the original path if not prefixed
        else:
            return self.DEFAULT_MOUNTPOINTS


class DriveFinder:
    def get_drives(self):
        """
        Retrieves a list of physical drives based on the operating system.
        Raises NotImplementedError for unsupported platforms.

        Returns:
            list of dict: A list of dictionaries, each representing a physical drive.
        """
        finder = self._get_platform_finder()
        return finder.get_physical_drives() if finder else []

    def _get_platform_finder(self):
        """
        Returns an instance of a platform-specific device finder.

        Returns:
            An instance of a subclass of DeviceFinder appropriate for the current OS, or None if unsupported.
        """
        if platform.system() == "Linux":
            return DriveFinderLinux()
        elif platform.system() == "Darwin":
            return DriveFinderDarwin()
        elif platform.system() == "Windows":
            raise NotImplementedError("Search drives in Windows is not implemented.")
        else:
            return None
