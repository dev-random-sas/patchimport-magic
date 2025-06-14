import sys
import tempfile
from pathlib import Path

from patchimport import parse_args, patcher, patchimport, unpatchimport

import pytest


# --- Test Data: The dummy module we will be patching ---
DUMMY_MODULE_CONTENT = """# This is LINE 1
CONSTANT = "original"

def original_function():  # This is LINE 4
    return "original result"

class MyClass:
    def method(self):
        return "original method"
"""

EXPECTED_HELP_MESSAGE = (
    "REMEMBER TO DO `import dummy_module` OR "
    "`from dummy_module import ...` AFTER THIS MAGIC CALL!"
)


@pytest.fixture
def dummy_module_path():
    """
    A pytest fixture to create a temporary dummy Python module for testing.
    This ensures that our tests are isolated and don't affect the actual filesystem.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Add the temporary directory to Python's path so it can be found
        sys.path.insert(0, tmpdir)

        module_path = Path(tmpdir) / "dummy_module.py"
        module_path.write_text(DUMMY_MODULE_CONTENT)

        # Yield the path to the tests
        yield module_path

        # Teardown: Clean up sys.path and unload the module
        sys.path.pop(0)
        if "dummy_module" in sys.modules:
            del sys.modules["dummy_module"]


def test_code_insertion(dummy_module_path, capteesys):
    """
    Tests if `patchimport` can correctly insert code into a module.
    """
    patch_code = "NEW_VARIABLE = 42\n\n\n\n\n\n"
    patchimport(line="dummy_module 2", cell=patch_code)

    import dummy_module

    assert hasattr(dummy_module, "NEW_VARIABLE")
    assert dummy_module.NEW_VARIABLE == 42
    assert dummy_module.CONSTANT == "original"
    assert dummy_module.original_function() == "original result"
    out, _ = capteesys.readouterr()
    assert EXPECTED_HELP_MESSAGE in out


def test_code_deletion(dummy_module_path, capteesys):
    """
    Tests if `patchimport` can correctly delete code from a module.
    """
    patch_code = "# Disabling original_function"
    patchimport(line="dummy_module 3 7", cell=patch_code)

    import dummy_module

    assert not hasattr(dummy_module, "original_function")
    assert hasattr(dummy_module, "MyClass")
    assert dummy_module.CONSTANT == "original"
    out, _ = capteesys.readouterr()
    assert EXPECTED_HELP_MESSAGE in out


def test_code_append(dummy_module_path, capteesys):
    """
    Tests if `patchimport` can correctly insert code into a module.
    """
    patch_code = "NEW_VARIABLE = 42"
    patchimport(line="dummy_module 10", cell=patch_code)

    import dummy_module

    assert hasattr(dummy_module, "NEW_VARIABLE")
    assert dummy_module.NEW_VARIABLE == 42
    assert dummy_module.CONSTANT == "original"
    assert dummy_module.original_function() == "original result"
    out, _ = capteesys.readouterr()
    assert EXPECTED_HELP_MESSAGE in out


def test_code_replacement(dummy_module_path, capteesys):
    """
    Tests if `patchimport` can correctly replace a block of code.
    """
    patch_code = '    return "patched result"'
    patchimport(line="dummy_module 5 6", cell=patch_code)

    import dummy_module

    assert dummy_module.original_function() == "patched result"
    assert dummy_module.CONSTANT == "original"
    assert dummy_module.MyClass().method() == "original method"
    out, _ = capteesys.readouterr()
    assert EXPECTED_HELP_MESSAGE in out


def test_patchimport_manytimes(dummy_module_path, capteesys):
    """
    Tests that `patchimport` does not modify previous imports of module,
    and that on each patch it starts from the original state.
    """
    import dummy_module as original

    patch_code = 'CONSTANT = "replaced"'
    patchimport(line="dummy_module 2 3", cell=patch_code)
    import dummy_module as patched

    patch_code = 'NEW_VARIABLE = "added"'
    patchimport(line="dummy_module 3", cell=patch_code)
    import dummy_module as repatched

    assert original.CONSTANT == "original"
    assert patched.CONSTANT == "replaced"
    assert repatched.CONSTANT == "original"

    assert not hasattr(original, "NEW_VARIABLE")
    assert not hasattr(patched, "NEW_VARIABLE")
    assert repatched.NEW_VARIABLE == "added"


def test_unpatchimport(dummy_module_path, capteesys):
    """
    Tests that `patchimport` does not modify previous imports of module,
    and that on each patch it starts from the original state.
    """
    patch_code = 'CONSTANT = "replaced"'
    patchimport(line="dummy_module 2 3", cell=patch_code)
    import dummy_module as patched

    unpatchimport(line="dummy_module")
    import dummy_module as unpatched

    assert patched.CONSTANT == "replaced"
    assert unpatched.CONSTANT == "original"


def test_parse_args():
    """
    Tests the argument parsing logic.
    """
    # Test insertion case
    args = parse_args("my_module 10")
    assert args.module == "my_module"
    assert args.start_line == 10
    assert args.end_line is None

    # Test replacement case
    args = parse_args("another.module 5 15")
    assert args.module == "another.module"
    assert args.start_line == 5
    assert args.end_line == 15


def test_patcher_logic():
    """
    Tests the core patcher function directly.
    """
    source = "line1\nline2\nline3\nline4"
    patch_text = "inserted_line_A\ninserted_line_B"

    # Test insertion
    new_source = patcher(
        source, start_line=1, end_line=1, patch=patch_text, log_function=None
    )
    assert new_source == "line1\ninserted_line_A\ninserted_line_B\nline2\nline3\nline4"

    # Test replacement
    new_source_2 = patcher(
        source, start_line=1, end_line=3, patch=patch_text, log_function=None
    )
    assert new_source_2 == "line1\ninserted_line_A\ninserted_line_B\nline4"


def test_invalid_line_numbers(capteesys):
    """
    Tests that the magic handles invalid line number arguments gracefully.
    """
    # Case 1: start_line < 1
    patchimport(line="dummy_module 0", cell="pass")
    out, _ = capteesys.readouterr()
    assert "Error: start_line must be at least 1" in out

    # Case 2: end_line <= start_line
    patchimport(line="dummy_module 10 5", cell="pass")
    out, _ = capteesys.readouterr()
    assert "Error: end_line must be greater than start_line" in out
