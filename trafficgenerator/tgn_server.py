"""
Classes and functions to manage a Server in the Testbed.
"""
import logging
import os
import socket
import subprocess
import time
from io import StringIO
from pathlib import Path
from typing import Optional, Union

import fabric.runners
from fabric import Connection
from invoke import ThreadException, UnexpectedExit
from paramiko.ssh_exception import NoValidConnectionsError, SSHException

from trafficgenerator.tgn_vmware import VMWare

logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger("invoke").setLevel(logging.WARNING)
logger = logging.getLogger("tgn.trafficgenerator")


class SshShell:
    """SSH connection to Server in the Testbed.

    :TODO: Consider extending Connection rather than using it.
    """

    def __init__(self, host: str, user: str, password: str) -> None:
        """Initialize Connection object.

        :param host: Hostname or ipaddress.
        :param user: Username.
        :param password: Password for user.
        """
        self.host = host
        self.user = user
        self.password = password

    def exec_cmd(self, cmd: str) -> fabric.runners.Result:
        """Execute the requested command.

        :param cmd: Command to run.
        """
        logger.debug(f"Executing command: {cmd}")
        with Connection(self.host, user=self.user, connect_kwargs={"password": self.password}) as connection:
            result = connection.run(cmd, hide=True)
        logger.debug(f"Command output: {result.stdout.strip()}")
        return result

    def put(self, local: Union[str, StringIO], remote: str) -> None:
        """Put a local file to the remote filesystem."""
        logger.info(f"Putting {local} to {remote}")
        with Connection(self.host, user=self.user, connect_kwargs={"password": self.password}) as connection:
            connection.put(local, remote)


class Server:
    """Server in the Testbed. Provides SSH and VMWare connectivity to the remote host."""

    def __init__(self, name: str, host: str, user: str, password: str, vmware: Optional[VMWare] = None) -> None:
        """Initialize SSH and VMWare objects.

        :param name: server name - if server is VM this should be the VM name, otherwise it can be any representative name.
        :param host: hostname or ipaddress.
        :param user: username.
        :param password: password for user.
        :param vmware: VMWare client in case the server is deployed on VMWare, else None.
        """
        self.name = name
        self.host = host
        self.user = user
        self.password = password
        self.ssh = SshShell(self.host, self.user, self.password)
        self.vmware = vmware

    def __repr__(self) -> str:
        """Server is represented by its name."""
        return f"{self.name}"

    def exec_cmd(self, cmd: str) -> fabric.runners.Result:
        """Execute the requested SSH command.

        :param cmd: Command to run.
        """
        return self.ssh.exec_cmd(cmd)

    def put(self, local: Union[Path, StringIO], remote: Path) -> None:
        """Put a local file to the remote filesystem."""
        self.ssh.put(local.as_posix() if isinstance(local, Path) else local, remote.as_posix())

    def power_on(self, wait: bool = True, timeout: Optional[int] = 60) -> None:
        """Power on virtual machine.

        :param wait: wait for system to come up or not
        :param timeout: time to wait for system to become pingable
        """
        if self.vmware:
            self.vmware.power_on(self.name)
            if wait:
                self.wait2up(timeout=timeout)
        else:
            raise ValueError(f"VMWare client not found for machine {self}")

    def shutdown(self, wait: bool = True, timeout: Optional[int] = 60) -> None:
        """Shutdown virtual machine.

        :param wait: wait for system to down or not
        :param timeout: time to wait for system to become non-pingable (go down).
        """
        if self.vmware:
            self.vmware.power_off(self.name, wait_off=False)
            if wait:
                self.wait2down(timeout=timeout)
        else:
            raise ValueError(f"VMWare client not found for machine {self}")

    def is_up(self) -> bool:
        """Ping to check if host is UP or not."""
        count_arg = "n" if os.name == "nt" else "c"
        ping_cmd = ["ping", self.host, f"-{count_arg}", "1", "-w", "1"]
        output = subprocess.run(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        state = (
            output.returncode == 0
            and b"Destination host unreachable" not in output.stdout
            and b"Request timed out" not in output.stdout
        )
        logger.debug(f"{self} state is {'UP' if state else 'DOWN'}")
        return state

    def wait2down(self, timeout: int = 30) -> None:
        """Wait for timeout seconds for host to become non-pingable (go down).

        :param timeout: wait for time in seconds
        """
        logger.info(f"Waiting for host {self} to go DOWN")
        for _ in range(timeout):
            if not self.is_up():
                logger.info(f"{self} is DOWN")
                return
            time.sleep(1)

        logger.exception(f"{self} did not went DOWN in {timeout} seconds")
        raise TimeoutError(f"{self} did not went DOWN in {timeout} seconds")

    def wait2up(self, timeout: int = 60) -> None:
        """Wait for timeout seconds for host to become pingable [come up].

        :param timeout: wait for time in seconds
        """
        logger.info(f"Waiting for host {self} to go UP")
        for _ in range(timeout):
            if self.is_up():
                logger.info(f"{self} is UP")
                return
            time.sleep(1)

        logger.exception(f"{self} did not went UP in {timeout} seconds")
        raise TimeoutError(f"{self} did not went UP in {timeout} seconds")

    def reboot(self, wait: bool = True, timeout: Optional[int] = 60) -> None:
        """Reboot a linux machine and wait for it to come up."""
        logger.info(f"Resetting {self}")
        if not self.is_up():
            self.power_on(wait, timeout)
            return
        try:
            self.exec_cmd("/usr/sbin/reboot")
        except (UnexpectedExit, ThreadException):
            pass
        if wait:
            self.wait_reboot(timeout)

    def wait_reboot(self, timeout: int = 60) -> None:
        """Wait for reboot."""
        for _ in range(timeout):
            try:
                with Connection(
                    self.host, user=self.user, connect_kwargs={"password": self.password}, connect_timeout=1
                ) as connection:
                    up_time = connection.run("uptime -p", hide=True).stdout.strip()
                # In some distros (like centos 7) if uptime < 1 the output will be "up", in others "up 0 minutes".
                if up_time == "up" or float(up_time.split()[1]) < timeout / 60:
                    return
            except (NoValidConnectionsError, socket.timeout, SSHException):
                pass
            time.sleep(1)
        raise TimeoutError(f"{self.host} did not reboot after {timeout} seconds")
