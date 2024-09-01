import platform
import json
import plistlib

from ..utils import execute_command

from .physical import DriveFinder
from .rclone import RcloneFinder
from .gocryptfs import GocryptfsFinder


class DeviceFinder:
    """
    Facilitates the discovery of physical and virtual (rclone) drives.
    Dynamically selects the appropriate method for the current operating system.
    """

    def __init__(self, label=None):
        self.label = label

    def get_all_devices(self):
        """
        Retrieves a list of all drives.

        Returns:
            list of dict: A list of dictionaries, each representing a drive.
        """

        finders = [DriveFinder(), RcloneFinder(), GocryptfsFinder()]
        drives = []
        for s in finders:
            drives.extend(s.get_drives())
        return drives

    def find_device(self, label=None, name=None, path=None):
        """
        Searches both physical and rclone drives for a device matching the given label or name or mountpoint (path).

        Args:
            label (str, optional): The label of the device to find. Defaults to the instance's label.
            name (str, optional): The name of the device to find.
            path (str, optional): The mountpoint of the device to find.

        Returns:
            list of dict: A list of dictionaries, each representing a found device.
        """
        label = label or self.label

        devices = self.get_all_devices()
        filtered_devices = []

        for device in devices:
            if name and device["name"] == name:
                filtered_devices.append(device)
            elif label and device["label"] == label:
                filtered_devices.append(device)
            elif path and path in device["mountpoints"]:
                filtered_devices.append(device)

        return filtered_devices
