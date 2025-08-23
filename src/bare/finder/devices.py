from __future__ import annotations

from typing import Any

from .gocryptfs import GocryptfsFinder
from .physical import DriveFinder
from .rclone import RcloneFinder


class DeviceFinder:
    """
    Facilitates the discovery of physical and virtual (rclone) drives.
    Dynamically selects the appropriate method for the current operating system.
    """

    def __init__(self, label: str | None = None) -> None:
        self.label = label

    def get_all_devices(self) -> list[dict[str, Any]]:
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

    def find_device(
        self, label: str | None = None, name: str | None = None, path: str | None = None
    ) -> list[dict[str, Any]]:
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
            if (
                name
                and device["name"] == name
                or label
                and device["label"] == label
                or path
                and path in device["mountpoints"]
            ):
                filtered_devices.append(device)

        return filtered_devices
