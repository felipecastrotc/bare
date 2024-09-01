import os
import platform
import subprocess
import re
import threading


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


def stream_reader(pipe, output_list):
    """Read from the pipe line by line and store the output in the provided list."""
    for line in iter(pipe.readline, ""):
        print(line, end="", flush=True)
        output_list.append(line)
    pipe.close()


def execute_command(command, env_vars=None, mask=None, ignore_error=False):
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

    # Initialize lists to capture standard output and error streams
    stdout_output = []
    stderr_output = []

    # Use subprocess to execute the command, capturing stdout and stderr
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        env=environment,
        universal_newlines=True,
    ) as process:

        # Create threads to read stdout and stderr to avoid blocking
        stdout_thread = threading.Thread(
            target=stream_reader, args=(process.stdout, stdout_output)
        )
        stderr_thread = threading.Thread(
            target=stream_reader, args=(process.stderr, stderr_output)
        )

        stdout_thread.start()
        stderr_thread.start()

        # Wait for the threads to finish reading the output streams
        stdout_thread.join()
        stderr_thread.join()

        # Wait for the process to complete execution
        process.wait()

    # Check the process exit code to determine if the command was successful
    if process.returncode != 0 and not ignore_error:
        raise Exception(f"Command failed with error: {''.join(stderr_output)}")

    return "".join(stdout_output)


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


def dict2args(args, double="--", single="-", join_double=" ", join_single=" "):
    def gen_arg(arg, val):
        # Determine the prefix for the argument name.
        arg_name = double + arg if len(arg) > 1 else single + arg

        # Determine the character to join the argument name and value.
        join = join_double if len(arg) > 1 else join_single

        # Return the formatted argument string by combining the argument name, join character, and value.
        return arg_name + join + str(val)

    out = []
    for k, v in args.items():
        if isinstance(v, list):
            # If the value is a list, generate an argument string for each item in the list.
            for item in v:
                out.append(gen_arg(k, item))
        else:
            # If the value is not a list, generate a single argument string.
            out.append(gen_arg(k, v))

    # Join all the generated argument strings into a single command-line string separated by spaces.
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

    output = execute_command("mount")

    mounts = []
    for line in output.splitlines():
        if platform.system() == "Linux":
            # For Linux, mount output is typically like:
            # /dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)
            match = re.match(r"(.+?) on (.+?) type (.+?) \((.+)\)", line)
            if match:
                device, mount_point, fstype, options = match.groups()
        elif platform.system() == "Darwin":
            # For macOS, mount output is typically like:
            # /dev/disk1s1 on / (apfs, local, read-only, journaled)
            match = re.match(r"(.+?) on (.+?) \((.+?), (.+)\)", line)
            if match:
                device, mount_point, fstype, options = match.groups()
                options = options.split(", ")
        else:
            continue

        if match:
            mounts.append(
                {
                    "src": device,
                    "dst": mount_point,
                    "fstype": fstype,
                    "args": "(" + " ".join(options) + ")",
                }
            )

    return mounts
