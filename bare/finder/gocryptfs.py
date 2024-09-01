import platform
from ..utils import parse_mount


class GocryptfsFinder:
    """
    A class dedicated to finding and formatting gocryptfs mounted drives on the system.
    """

    def get_drives(self):
        """
        Public method to get formatted gocryptfs drive details.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with formatted drive details.
        """
        return self._format_finder(self._get_gocryptfs_mounted())

    def _get_mounted_by_os(self):
        """
        Private method to get mount details from the operating system.

        Returns:
            List[Dict[str, str]]: A list of mount dictionaries.

        Raises:
            NotImplementedError: If the OS is not Linux or Darwin (macOS).
        """
        os_type = platform.system()
        if os_type in ["Linux", "Darwin"]:
            return parse_mount()
        else:
            raise NotImplementedError(
                "Mount point detection not implemented for Windows."
            )

    def _get_gocryptfs_mounted(self):
        """
        Filters the mounted drives to find those specifically using 'fuse.gocryptfs'.

        Returns:
            List[Dict[str, str]]: A filtered list of gocryptfs mount dictionaries.
        """
        mounts = self._get_mounted_by_os()
        return [mount for mount in mounts if mount["fstype"] == "fuse.gocryptfs"]

    def _format_finder(self, drives):
        """
        Formats the list of drives into a specified structure.

        Args:
            drives (List[Dict[str, str]]): List of gocryptfs mount dictionaries.

        Returns:
            List[Dict[str, Any]]: A list of formatted drive details.
        """
        formatted = []
        for drive in drives:
            new_drive = {
                "name": "gocryptfs",
                "label": drive["src"],
                "fstype": drive["fstype"],
                "mountpoints": [drive["dest"]],
            }
            formatted.append(new_drive)
        return formatted
