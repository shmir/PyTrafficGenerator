"""
Base class and utilities for TGN Python Tcl wrapper.
"""
import json
import logging
from os import path
from typing import Dict, List, Optional

from trafficgenerator.tgn_object import TgnObject
from trafficgenerator.tgn_utils import new_log_file

# Tcl is must only if the test chooses to use Tcl API, so it is OK if Tcl is not installed (e.g for some Linux
# installations). If Tcl interpreter is required and not installed it will fail anyway...
try:
    from tkinter import Tcl

    from _tkinter import TclError

    tcl_interp_g: "TgnTk" = None
    """ Global Tcl interpreter for Tcl based utilities. Does not log its operations. """
except ModuleNotFoundError:
    pass


def tcl_str(string: str = "") -> str:
    """Return Tcl string surrounded by {}.

    :param string: Python string.
    """
    return " {" + string + "} "


def tcl_file_name(name: str) -> str:
    """Return normalized file name with forward slashes.

    :param name: file name.
    """
    return tcl_str(path.normpath(name).replace("\\", "/"))


def get_args_pairs(arguments: Dict[str, object]) -> str:
    """Return Tcl list of argument pairs <-key, value> to be used in TGN API commands.

    :param arguments: Python dictionary of TGN API command arguments <key, value>.
    """
    return " ".join(" ".join(["-" + k, tcl_str(str(v))]) for k, v in arguments.items())


def build_obj_ref_list(objects: List[TgnObject]) -> str:
    """Return Tcl list of all requested objects references.

    :param objects: Python list of requested objects.
    """
    return " ".join([o.ref for o in objects])


def tcl_list_2_py_list(tcl_list: str) -> list:
    """Recursievely convert embedded Tcl list to embedded Python list using Tcl interpreter.

    :param str tcl_list: string representing the Tcl list.
    """
    if not tcl_list:
        return []

    try:
        return json.loads(tcl_list)
    except json.decoder.JSONDecodeError:
        try:
            python_list = tcl_interp_g.eval("join " + tcl_list + " LiStSeP").split("LiStSeP")
        except TclError:
            python_list = tcl_interp_g.eval("join " + tcl_str(tcl_list) + " LiStSeP").split("LiStSeP")
        if len([i for i in python_list if "{" in i]) == 0:
            return python_list
        return [tcl_list_2_py_list(e) for e in python_list]


def py_list_to_tcl_list(py_list: list) -> str:
    """Convert Python list to Tcl list using Tcl interpreter.

    :param py_list: Python list.
    """
    py_list_str = [str(s) for s in py_list]
    return tcl_str(tcl_interp_g.eval("split" + tcl_str("\t".join(py_list_str)) + "\\t"))


class TgnTk:
    """Native Python Tk interpreter."""

    def __init__(self) -> None:
        """Init Tcl interpreter."""
        self.tcl = Tcl()

    def eval(self, command: str) -> str:  # noqa: A003
        """Execute Tcl eval command."""
        return self.tcl.eval(command)


class TgnTclWrapper:
    """Tcl connectivity for TGN projects."""

    def __init__(self, logger: logging.Logger, tcl_interp: Optional[TgnTk] = None) -> None:
        """Init Python Tcl package.

        Add logger to log Tcl commands only.
        This creates a clean Tcl script that can be used later for debug.
        We assume that there might have both multiple Tcl sessions simultaneously so we add suffix to create
        multiple distinguished Tcl scripts.
        """
        if not logger:
            logger = logging.getLogger("dummy")
        self.logger = logger
        self.tcl_script = new_log_file(self.logger, self.__class__.__name__)

        if not tcl_interp:
            self.tcl_interp = TgnTk()
        else:
            self.tcl_interp = tcl_interp
        global tcl_interp_g  # pylint: disable=invalid-name, global-statement
        tcl_interp_g = self.tcl_interp
        self.rc: str = None

    def eval(self, command: str) -> str:  # noqa: A003
        """Execute Tcl command.

        Write the command to tcl script (.tcl) log file.
        Execute the command.
        Write the command and the output to general (.txt) log file.

        :param command: Command to execute.
        :returns: command raw output.
        """
        self.logger.debug(command)
        if self.tcl_script:
            self.tcl_script.info(command)
        self.rc = self.tcl_interp.eval(command)
        self.logger.debug(f"\t{self.rc}")
        return self.rc

    def source(self, script_file: str) -> None:
        """Tcl source command."""
        self.eval("source " + tcl_file_name(script_file))
