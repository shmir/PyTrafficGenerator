"""
Base class and utilities for TGN Python Tcl wrapper.
"""

from os import path
import logging
import time
import re
from threading import Thread
from queue import Queue
import json
from typing import Dict, List

from trafficgenerator.tgn_utils import new_log_file
from trafficgenerator.tgn_object import TgnObject

# Tcl is must only if the test chooses to use Tcl API so it is OK if Tcl is not installed (e.g for
# some Linux installations). If Tcl interpreter is required and not installed it will fail anyway...
try:
    from tkinter import Tcl
except Exception as _:
    pass


def tcl_str(string: str = '') -> str:
    """
    :param string: Python string.
    :returns: Tcl string surrounded by {}.
    """

    return ' {' + string + '} '


def tcl_file_name(name: str) -> str:
    """
    :param name: file name.
    :returns: normalized file name with forward slashes.
    """

    return tcl_str(path.normpath(name).replace('\\', '/'))


def get_args_pairs(arguments: Dict[str, object]) -> str:
    """
    :param arguments: Python dictionary of TGN API command arguments <key, value>.
    :returns: Tcl list of argument pairs <-key, value> to be used in TGN API commands.
    """

    return ' '.join(' '.join(['-' + k, tcl_str(str(v))]) for k, v in arguments.items())


def build_obj_ref_list(objects: List[TgnObject]) -> str:
    """
    :param objects: Python list of requested objects.
    :returns: Tcl list of all requested objects references.
    """

    return ' '.join([o.ref for o in objects])


tcl_interp_g = None
""" Global Tcl interpreter for Tcl based utilities. Does not log its operations. """


def tcl_list_2_py_list(tcl_list: str) -> List:
    """ Convert Tcl [embedded] list to Python [embedded] list using Tcl interpreter.

    :param str tcl_list: string representing the Tcl list.
    :return: Python list equivalent to the Tcl list.
    :rtye: list
    """

    if not tcl_list:
        return []

    try:
        return json.loads(tcl_list)
    except Exception as _:
        try:
            python_list = tcl_interp_g.eval('join ' + tcl_list + ' LiStSeP').split('LiStSeP')
        except Exception as _:
            python_list = tcl_interp_g.eval('join ' + tcl_str(tcl_list) + ' LiStSeP').split('LiStSeP')
        if len([i for i in python_list if '{' in i]) == 0:
            return python_list
        return [tcl_list_2_py_list(e) for e in python_list]


def py_list_to_tcl_list(py_list):
    """ Convert Python list to Tcl list using Tcl interpreter.

    :param py_list: Python list.
    :type py_list: list
    :return: string representing the Tcl string equivalent to the Python list.
    """

    py_list_str = [str(s) for s in py_list]
    return tcl_str(tcl_interp_g.eval('split' + tcl_str('\t'.join(py_list_str)) + '\\t'))


class TgnTk:
    """ Native Python Tk interpreter. """

    def __init__(self):
        self.tcl = Tcl()

    def eval(self, command):
        return self.tcl.eval(command)


class TgnTkMultithread(Thread):
    """ Native Python Tk interpreter with multithreading. """

    _is_running = True

    def __init__(self):
        super(self.__class__, self).__init__()
        self.in_q = Queue()
        self.out_q = Queue()
        self.tcl = None

    def run(self):
        if not self.tcl:
            self.tcl = Tcl()
        while self._is_running:
            if not self.in_q.empty():
                command = self.in_q.get()
                try:
                    rc = self.tcl.eval(command)
                    self.out_q.put(rc)
                except Exception as e:
                    self.out_q.put(e)
            time.sleep(1)

    def stop(self):
        self._is_running = False

    def eval(self, command):
        self.in_q.put(command)
        while self.out_q.empty():
            time.sleep(1)
        rc = self.out_q.get()
        if isinstance(rc, Exception):
            raise rc
        return rc


class TgnTclConsole:
    """ Tcl interpreter over console.

    Current implementation is a sample extracted from actual project where the console is telnet to Windows machine.
    """

    def __init__(self, con, tcl_exe):
        """ Start Tcl interpreter on console.

        :param con: console.
        :param tcl_exe: full path to Tcl exe.
        """
        super(TgnTclConsole, self).__init__()
        self._con = con
        self._con.set_prompt_match_expression('% ')
        self._con.send_cmd(tcl_exe)

    def eval(self, command):
        """
        @summary: Evaluate Tcl command.

        @param command: command to evaluate.
        @return: command output.
        """
        # Some operations (like take ownership) may take long time.
        con_command_out = self._con.send_cmd(command, timeout=256)
        if 'ERROR_SEND_CMD_EXIT_DUE_TO_TIMEOUT' in con_command_out:
            raise Exception('{} - command timeout'.format(command))
        command = command.replace('\\', '/')
        con_command_out = con_command_out.replace('\\', '/')
        command = command.replace('(', r'\(').replace(')', r'\)')
        command = command.replace('{', r'\{').replace('}', r'\}')
        m = re.search(command + '(.*)' + '%', con_command_out, re.DOTALL)
        command_out = m.group(1).strip()
        if 'couldn\'t read file' in command_out or 'RuntimeError' in command_out:
            raise Exception(command_out)
        return command_out

    def disconnect(self):
        self._con.set_prompt_match_expression('C:.*>')
        self._con.send_cmd('exit')


class TgnTclWrapper:
    """ Tcl connectivity for TGN projects. """

    def __init__(self, logger: logging.Logger, tcl_interp=None):
        """ Init Python Tk package.

        Add logger to log Tcl commands only.
        This creates a clean Tcl script that can be used later for debug.
        We assume that there might have both multiple Tcl sessions simultaneously so we add suffix to create
        multiple distinguished Tcl scripts.
        """

        if not logger:
            logger = logging.getLogger('dummy')
        self.logger = logger
        self.tcl_script = new_log_file(self.logger, self.__class__.__name__)

        if not tcl_interp:
            self.tcl_interp = TgnTk()
        else:
            self.tcl_interp = tcl_interp
        global tcl_interp_g
        tcl_interp_g = self.tcl_interp

    def eval(self, command):
        """ Execute Tcl command.

        Write the command to tcl script (.tcl) log file.
        Execute the command.
        Write the command and the output to general (.txt) log file.

        :param command: Command to execute.
        :returns: command raw output.
        """

        if self.logger.handlers:
            self.logger.debug(command)
        if self.tcl_script:
            self.tcl_script.info(command)
        self.rc = self.tcl_interp.eval(command)
        if self.logger.handlers:
            self.logger.debug('\t' + self.rc)
        return self.rc

    def source(self, script_file):
        self.eval('source ' + tcl_file_name(script_file))
