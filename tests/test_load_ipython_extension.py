from unittest.mock import MagicMock

from patchimport import load_ipython_extension, patchimport, unpatchimport


def test_load_ipython_extension_registers_magics():
    """
    Tests that load_ipython_extension registers the patchimport and
    unpatchimport magics with the correct names and kinds.
    """
    ipython = MagicMock()

    load_ipython_extension(ipython)

    # patchimport should be registered as a cell magic
    ipython.register_magic_function.assert_any_call(
        patchimport, magic_kind="cell", magic_name="patchimport"
    )

    # unpatchimport should be registered as a line_cell magic
    ipython.register_magic_function.assert_any_call(
        unpatchimport, magic_kind="line_cell", magic_name="unpatchimport"
    )

    # no extra registrations
    assert ipython.register_magic_function.call_count == 2
