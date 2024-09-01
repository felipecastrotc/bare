import os
import platform
import subprocess

import subprocess
import os
import platform


def setup_environment(env_vars=None):
    """
    Prepare and return the environment settings for the subprocess.

    Args:
    env_vars (dict, optional): Dictionary of environment variables and their values.

    Returns:
    dict: A dictionary representing the environment.
    """
    environment = dict(os.environ.copy())
    if env_vars:
        environment.update(env_vars)
    return environment


def modify_command_for_os(command, mask=None):
    """
    Modify the command based on the operating system, such as using proot on Linux.

    Args:
    command (str): The initial command.
    mask (str, optional): Path to be masked using proot on Linux.

    Returns:
    str: The potentially modified command.
    """
    os_type = platform.system()
    if os_type == "Linux" and mask:
        # mask = ["True path", "masked path"]
        return f"proot -b {mask[0]}:{mask[1]} {command}"
    return command


def execute_command(command, env_vars=None, mask=None):
    """
    Execute a terminal command with optional environment variables and path masking,
    and return the output.

    Args:
    command (str): The command that will be executed.
    env_vars (dict, optional): Dictionary of environment variables and their values.
    mask (str, optional): Path to be masked using proot on Linux.

    Returns:
    str: The standard output from the command execution.

    Raises:
    Exception: If the command execution fails, an exception is raised with the error message.
    """
    environment = setup_environment(env_vars)
    command = modify_command_for_os(command, mask)

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        env=environment,
    )
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode("utf-8")
        raise Exception(f"Command failed with error: {error_msg}")

    return stdout.decode("utf-8")


def execute_command_test(command, env_vars=None, mask=None):
    """
    Execute a terminal command with optional environment variables and path masking,
    and return the output.

    Args:
    command (str): The command that will be executed.
    env_vars (dict, optional): Dictionary of environment variables and their values.
    mask (str, optional): Path to be masked using proot on Linux.

    Returns:
    str: The standard output from the command execution.

    Raises:
    Exception: If the command execution fails, an exception is raised with the error message.
    """
    environment = setup_environment(env_vars)
    command = modify_command_for_os(command, mask)

    print(f"I was supposed to run: {command}")
    return command


def build_command(command, *args):
    """
    Build a shell command by concatenating a base command with additional arguments,
    ensuring proper spacing between each component.

    Args:
    command (str): The base command to be executed.
    *args: A variable number of additional arguments that will be appended to the command.

    Returns:
    str: The fully constructed command string.
    """
    # Ensure that the base command is a string
    if not isinstance(command, str):
        raise ValueError("The command must be a string.")

    # Convert all additional arguments to strings and create the full command
    args_str = " ".join(str(arg) for arg in args)
    full_command = f"{command} {args_str}".strip()

    return full_command


def get_hostname():
    """Retrieve the current machine's hostname.

    Returns:
        str: The hostname of the machine.
    """
    if platform.system() == "Darwin":
        hostname_full = platform.node()
        hostname = hostname_full.split(".local")[0]
    else:
        hostname = platform.node()
    return hostname


def dict2args(args, double="--", single="-"):
    out = []
    for k, v in args.items():
        if isinstance(v, list):
            # If the value is a list, repeat the argument for each item in the list
            for item in v:
                out.append(double + k if len(k) > 1 else single + k)
                out.append(str(item))
        else:
            # Handle single value arguments
            out.append(double + k if len(k) > 1 else single + k)
            out.append(str(v))
    return " ".join(out)


def parse_mount():
    """
    Parses the output of the 'mount' command to extract details about each mount.

    Retrieves information about all the current mount points in the system by
    executing the 'mount' command. It then parses each line of the output to
    extract source, destination, filesystem type, and mount arguments into a
    structured dictionary format.

    Returns:
        list of dict: A list of dictionaries, where each dictionary contains
                      the details of a mount point with keys 'src', 'dest',
                      'fstype', and 'args'.
    """
    info = execute_command("mount")
    parse = info.split("\n")
    out = []

    for p in parse:
        if p:  # Ensure the line is not empty
            src, data = p.split(" on ")
            dst, data = data.split(" type ")
            fstype, args = data.split(" (")
            out.append({"src": src, "dest": dst, "fstype": fstype, "args": "(" + args})

    return out
