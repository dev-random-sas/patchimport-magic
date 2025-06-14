import argparse
import shlex
import sys
from functools import partial
from importlib import util
from typing import NamedTuple, Optional


# Source: https://stackoverflow.com/a/41863728/1460016
def modify_and_import(module_name, package, modification_func):
    spec = util.find_spec(module_name, package)
    source = spec.loader.get_source(module_name)
    new_source = modification_func(source)
    spec.origin = None  # TODO: Make Jupyter stop finding the (now wrong) code on ??
    spec.cached = None
    module = util.module_from_spec(spec)
    codeobj = compile(new_source, f"<patched {module.__spec__.origin}>", "exec")
    exec(codeobj, module.__dict__)
    sys.modules[module_name] = module
    return module


help_message = """Apply a patch to module MODULE.
If only START_LINE is provided lines in the cell will be inserted before it.
If END_LINE is also provided original lines upto (but not including) it will be deleted.
After usage, do `import MODULE` or `from MODULE import ...` to use the patched module.
"""


class PatchArgs(NamedTuple):
    module: str
    start_line: int
    end_line: Optional[int]


def parse_args(line: str) -> PatchArgs:
    """Parse arguments from line.

    This returns the parsed arguments or throws SystemExit if parsing fails."""
    parser = argparse.ArgumentParser(prog="%%patch_import", description=help_message)
    parser.add_argument("module", help="Module name to patch", metavar="MODULE")
    parser.add_argument(
        "start_line",
        type=int,
        help="Starting line number",
        metavar="START_LINE",
    )
    parser.add_argument(
        "end_line",
        nargs="?",
        type=int,
        help="Ending line number (optional)",
        metavar="END_LINE",
    )

    args = parser.parse_args(shlex.split(line))
    return PatchArgs(
        module=args.module, start_line=args.start_line, end_line=args.end_line
    )


def patcher(source, start_line, end_line, patch, log_function=print):
    lines = source.splitlines()
    patch_lines = patch.splitlines()
    # TODO: Add support for autoindent
    # TODO: Ensure we don't fall off the end. See how to abort the process in that case.
    new_lines = [*(lines[:start_line]), *patch_lines, *(lines[end_line:])]
    new_src = "\n".join(new_lines)

    # For logging line numbers get incremented by 1 to match what users see in editors.
    if callable(log_function):
        modified_end = start_line + len(patch_lines)
        preview_lines = [
            f"{i+1:3} {new_lines[i]}" for i in range(max(start_line - 3, 0), start_line)
        ]
        preview_lines += [
            f"{i+1:3}+{new_lines[i]}" for i in range(start_line, modified_end)
        ]
        try:
            if end_line <= modified_end:
                # We inserted at least what we deleted, so we print from new_lines
                preview_lines += [
                    f"{i+1:3} {new_lines[i]}"
                    for i in range(modified_end, modified_end + 3)
                ]
            else:
                # We deleted more than we inserted, so we print from original lines
                preview_lines += [
                    f"{i+1:3}-{lines[i]}" for i in range(modified_end, end_line)
                ]
                preview_lines += [
                    f"{i+1:3} {lines[i]}" for i in range(end_line, end_line + 3)
                ]
        except IndexError:
            # We fell off the end, and that's ok.
            pass
        log_function(f"Patch applied from line {start_line+1} to {end_line+1}:\n")
        log_function("\n".join(preview_lines))

    return new_src


def patchimport(line, cell):
    """
    A cell magic to apply a patch before importing a module.

    Usage:
    %%patchimport MODULE START_LINE [END_LINE]
    code to be inserted/replaced
    many lines if needed
    # %

    Examples:

    %%patchimport my_module 10
    breakpoint() # This will be inserted right before line 10
    # %

    %%patchimport my_module 5 10
    # Start deleting code at line 5, and stop before line 10
    # %
    """
    try:
        module, start_line, end_line = parse_args(line)
    except SystemExit:
        # Parser bailed, but Jupyter would complain if it exited, so we return instead.
        return

    # Validate arguments
    if start_line < 1:
        print("Error: start_line must be at least 1")
        return

    if end_line is not None:
        if end_line <= start_line:
            print("Error: end_line must be greater than start_line")
            return
    else:
        # If end_line not provided, default to start_line (insert without deleting)
        end_line = start_line

    modify_and_import(
        module,
        None,
        partial(
            patcher,
            start_line=start_line - 1,
            end_line=end_line - 1,
            patch=cell,
            log_function=print,
        ),
    )
    print(
        "REMEMBER TO DO "
        f"`import {module}` OR `from {module} import ...` "
        "AFTER THIS MAGIC CALL!"
    )
    return


def unpatchimport(line, cell=None):
    """
    A cell magic to unapply patches previously applied by %%patch_import.

    Usage:
    %unpatchimport MODULE
    # %

    Examples:

    %%patchimport my_module 10
    breakpoint() # This will be inserted right before line 10
    # %

    %unpatchimport my_module
    # % # No more breakpoint()
    """
    line = shlex.split(line)  # Get the module name from the line
    if len(line) != 1:
        print("Usage: %unpatchimport MODULE")
        return
    module = line[0]

    modify_and_import(
        module,
        None,
        lambda s: s,  # No changes, just re-import the original source
    )
    print(
        "REMEMBER TO DO "
        f"`import {module}` OR `from {module} import ...` "
        "AFTER THIS MAGIC CALL!"
    )
    return


# TODO: Add support for diffs


def load_ipython_extension(ipython):
    ipython.register_magic_function(
        patchimport, magic_kind="cell", magic_name="patchimport"
    )
    ipython.register_magic_function(
        unpatchimport, magic_kind="line_cell", magic_name="unpatchimport"
    )


__all__ = [
    "patchimport",
    "unpatchimport",
    "load_ipython_extension",
]
