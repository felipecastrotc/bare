import os
from ..finder.devices import DeviceFinder
from ..mount_manager import MountManager
from ..utils import execute_command, get_hostname, setup_environment


class Base:
    """
    Base class for managing backup operations, including environment setup,
    password management, and mounting devices.

    Attributes:
        label (str): Identifier for the device or mount point.
        hostname (str): Hostname of the current machine.
        name (str): Optional session name.
        env (dict): Environment variables for the process.
        mount_drive (MountDrive): Instance for managing mount operations.
    """

    def __init__(self, hostname=None, name=None, check_hostname=True):
        self.env = setup_environment()
        self.name = name or "default_session"

        self.hostname = self.confirm_hostname(hostname, check_hostname)

    def confirm_hostname(self, hostname, check=True):
        """
        Confirms if the provided hostname matches the current machine's hostname.
        Prompts the user for confirmation if different, allowing to exit or continue.

        Parameters:
            hostname (str): The hostname to confirm.

        Returns:
            str: The confirmed hostname or the current machine's hostname if none provided.
        """
        if check:
            current_hostname = get_hostname()

            if hostname and hostname != current_hostname:
                print("The passed hostname is different from the current hostname!")
                print("You may overwrite a backup that's not yours.")
                if input("Do you want to continue? (y/n) ").lower().strip()[:1] == "n":
                    exit()
            return hostname or current_hostname
        else:
            return hostname
