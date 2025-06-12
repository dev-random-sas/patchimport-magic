import sys
from importlib import util
from functools import partial
import argparse
import shlex
from typing import NamedTuple

from IPython.core.magic import register_cell_magic


# Source: https://stackoverflow.com/a/41863728/1460016
def modify_and_import(module_name, package, modification_func):
    spec = util.find_spec(module_name, package)
    source = spec.loader.get_source(module_name)
    new_source = modification_func(source)
    module = util.module_from_spec(spec)
    codeobj = compile(new_source, module.__spec__.origin, "exec")
    exec(codeobj, module.__dict__)
    sys.modules[module_name] = module
    return module


help_message = (
    "Apply a patch to module MODULE.\n"
    "If only START_LINE is provided lines in the cell will be inserted before it.\n"
    "If END_LINE is also provided original lines upto (but not including) it will be deleted.\n"
    "After usage, do `import MODULE` or `from MODULE import ...` to use the patched module.\n"
)


class PatchArgs(NamedTuple):
    module: str
    start_line: int
    end_line: int | None


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

    args = parser.parse_known_args(shlex.split(line))
    return PatchArgs(
        module=args.module, start_line=args.start_line, end_line=args.end_line
    )


def patchimport(line, cell):
    """
    A cell magic to apply a patch before importing a module.

    Usage:
    %%patch_import MODULE START_LINE [END_LINE]
    code to be inserted/replaced
    many lines if needed
    # %

    Examples:

    %%patch_import my_module 10
    breakpoint() # This will be inserted right before line 10
    # %

    %%patch_import my_module 5 10
    # Start deleting code at line 5, and stop before line 10
    # %
    """
    try:
        module, start_line, end_line = parse_args(line)
    except SystemExit as e:
        return  # Parser bailed, but Jupyter would complain if it exited, so we return instead.

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

    def patcher(source, start_line, end_line, patch):
        lines = source.splitlines()
        patch_lines = patch.splitlines()
        new_lines = [*(lines[:start_line]), *patch_lines, *(lines[end_line:])]
        new_src = "\n".join(new_lines)

        modified_end = start_line + len(patch_lines)
        preview_lines = [
            f"{i+1:3} {new_lines[i]}" for i in range(start_line - 3, start_line)
        ]
        preview_lines += [
            f"{i+1:3}+{new_lines[i]}" for i in range(start_line, modified_end)
        ]
        if (
            end_line <= modified_end
        ):  # We inserted at least more than we deleted, so we print from new_lines
            preview_lines += [
                f"{i+1:3} {new_lines[i]}" for i in range(modified_end, modified_end + 3)
            ]
        else:  # We deleted more than we inserted, so we print from original lines
            preview_lines += [
                f"{i+1:3}-{lines[i]}" for i in range(modified_end, end_line)
            ]
            preview_lines += [
                f"{i+1:3} {lines[i]}" for i in range(end_line, end_line + 3)
            ]
        print(
            f"REMEMBER TO DO `import {module}` OR `from {module} import ...` AFTER THIS MAGIC CALL!"
        )
        print(f"Patch applied from line {start_line+1} to {end_line+1}:\n")
        print("\n".join(preview_lines))

        return new_src

    modify_and_import(
        module,
        None,
        partial(patcher, start_line=start_line - 1, end_line=end_line - 1, patch=cell),
    )


def load_ipython_extension(ipython):
    register_cell_magic(patchimport)


__all__ = ["patchimport"]
