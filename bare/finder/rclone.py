import platform

from ..utils import execute_command


class RcloneFinder:
    """
    Facilitates the discovery of rclone mounted drives.
    Utilizes the `rclone listremotes` command to list all configured remotes and identifies
    their mount points on Unix-like operating systems.
    """

    def get_drives(self):
        """
        Retrieves a list of mounted rclone drives, including their labels and filesystem type.
        Attempts to identify the mount points for each detected rclone remote.

        Returns:
            list of dict: A list of dictionaries, each representing a mounted rclone drive
                          with keys for name, label, fstype, and mountpoints.
        """
        listremotes_command = "rclone listremotes"
        remotes_output = execute_command(listremotes_command).strip()

        if remotes_output:
            remotes = remotes_output.split("\n")

            found_remotes = [
                {"name": "rclone", "label": remote, "fstype": "fuse.rclone"}
                for remote in remotes
                if remote
            ]
            return self._add_mountpoint(found_remotes)
        else:
            return []

    def _add_mountpoint(self, mounts):
        """
        Adds mount point information to each rclone drive based on the operating system.

        Args:
            mounts (list of dict): The list of rclone drives without mount points.

        Returns:
            list of dict: The updated list of rclone drives, including mount points.
        """
        os_type = platform.system()
        if os_type in ["Linux", "Darwin"]:
            mountpoints = self.get_rclone_mountpoint_unix()
        else:
            raise NotImplementedError(
                "Mount point detection not implemented for Windows."
            )

        for mount in mounts:
            mount["mountpoints"] = [mountpoints.get(mount["label"], [])]
        return mounts

    def get_rclone_mountpoint_unix(self):
        """
        Retrieves rclone mount points on Unix-like operating systems by parsing the output of
        the `ps` command to find running rclone mount processes.

        Returns:
            dict: A dictionary mapping each rclone label to its mount point path.
        """
        output = execute_command("ps -aux | grep 'rclone mount'").split("\n")
        mountpoints = {}

        for line in output:
            if "rclone mount" in line:
                parts = line.split()
                # Assumes label is always the first argument and path the second after 'rclone mount'
                idx = [i for i, s in enumerate(parts) if "mount" in s][0]
                if len(parts) > idx + 2:
                    label = parts[parts.index("mount") + 1]
                    path = parts[parts.index("mount") + 2]
                    mountpoints[label] = path

        return mountpoints
