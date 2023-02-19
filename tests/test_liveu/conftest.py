"""
Standard pytest fixtures and hooks definition file.
"""
import importlib.util
import sys
import types
from os import walk
from pathlib import Path

# pylint: disable=redefined-outer-name


def pytest_addoption(parser):
    parser.addoption("--speed", type=int, default=None, action="append", help="Speed of the test")
    parser.addoption("--delay", type=int, default=None, action="append", help="Delay of the test")


def pytest_generate_tests(metafunc):
    py_files = []
    for root, _, files in walk(Path(__file__).parent):
        py_files += [Path(root).joinpath(f).as_posix() for f in files if f.endswith(".py")]
    print(f"py_files: {py_files}")
    configs = []
    for py_file in py_files:
        module_object = import_source_file(py_file, py_file.replace("/", ".").replace(".py", ""))
        configs += [
            getattr(module_object, d)
            for d in dir(module_object)
            if isinstance(getattr(module_object, d), dict) and d.startswith("test_")
        ]
    for option in ["speed", "delay"]:
        if metafunc.config.getoption(f"--{option}") is not None:
            configs = [c for c in configs if c[option] in metafunc.config.getoption(f"--{option}")]
    metafunc.parametrize("klara", configs)


def import_source_file(fname: Path, modname: str) -> types.ModuleType:
    """
    Import a Python source file and return the loaded module.

    Args:
        fname: The full path to the source file.  It may container characters like `.`
            or `-`.
        modname: The name for the loaded module.  It may contain `.` and even characters
            that would normally not be allowed (e.g., `-`).
    Return:
        The imported module

    Raises:
        ImportError: If the file cannot be imported (e.g, if it's not a `.py` file or if
            it does not exist).
        Exception: Any exception that is raised while executing the module (e.g.,
            :exc:`SyntaxError).  These are errors made by the author of the module!
    """
    # https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    spec = importlib.util.spec_from_file_location(modname, fname)
    if spec is None:
        raise ImportError(f"Could not load spec for module '{modname}' at: {fname}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    try:
        spec.loader.exec_module(module)
    except FileNotFoundError as e:
        raise ImportError(f"{e.strerror}: {fname}") from e
    return module
