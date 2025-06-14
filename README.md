# patchimport-magic

[![Build Status](https://img.shields.io/github/actions/workflow/status/dev-random-sas/patchimport-magic/pypi.yml)](https://github.com/dev-random-sas/patchimport-magic)
[![PyPI - Version](https://img.shields.io/pypi/v/patchimport-magic)](https://pypi.org/project/patchimport-magic)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/patchimport-magic)](https://pypistats.org/packages/patchimport-magic)
![PyPI - License](https://img.shields.io/pypi/l/patchimport-magic)

IPython magic to patch modules before you import them.

`patchimport-magic` provides a cell magic (`%%patchimport`) that allows you to apply quick, in-memory patches to any installed Python module directly from a Jupyter Notebook or IPython session. This is incredibly useful for rapid debugging, performance profiling, experimenting with library internals without forking, or testing a potential fix on the fly.

---

## 🤔 Why?

Have you ever wanted to:

- **Quickly A/B test a function's performance** with `%%timeit`?
- **Add a `print` statement** inside a third-party library function to see what's going on?
- **Test a one-line fix** for a bug without cloning and reinstalling the entire package?
- **Experiment with a function's behavior** by temporarily changing its source code?

`patchimport-magic` lets you do all of this and more, right from your notebook.

---

## 🚀 Installation

Install the package from PyPI:

```bash
pip install patchimport-magic
```

---

## ✍️ Usage

First, load the extension in your IPython or Jupyter environment.

```python
%load_ext patchimport
```

The magic command has two main forms:

1.  **Inserting Code**: `%%patchimport <module_name> <start_line>`
2.  **Replacing Code**: `%%patchimport <module_name> <start_line> <end_line>`

After running the magic cell, you **must import the module in a new cell** for the changes to take effect.

You can also do `%unpatchimport <module_name>` to revert your patch.

### Example 1: Replacing Code

Let's modify the behavior of `random.choice()`. We can patch it to always return the _first_ element of a sequence by replacing its original implementation.

```python
# %%
%load_ext patchimport
!grep -n -A10 -e 'def choice(' /usr/lib/python3.9/random.py
# We find out the return we want to replace is in line 346 and has 8 spaces indentation
# %%
%%patchimport random 346 347
        return seq[0] # Always return the first element!

# %%
import random

my_list = ['apple', 'banana', 'cherry']
print(f"Patched random.choice: {random.choice(my_list)}")
```

### Example 3: A/B Performance Testing with `%%timeit`

This is where `patchimport-magic` really shines. Imagine you have written a utility module and suspect one of its functions is slow. You can quickly test an alternative implementation without changing the file.

**Scenario:** Let's say you have this file, `my_utility_module.py`:

```python
# my_utility_module.py
def find_common_elements(list1, list2):
    """Finds common elements using a slow, nested loop approach."""
    common = []
    for item in list1:
        if item in list2: # O(n) lookup for lists is slow!
            common.append(item)
    return common
```

Now, in your notebook, first time the original, slow version.

```python
# In your Notebook:

# 1. Create some data
import my_utility_module

data = list(range(1000))
sample_to_find = list(range(500, 1500))

# 2. Time the original implementation
print("Timing original (list-based) implementation:")
%timeit my_utility_module.find_common_elements(data, sample_to_find)
```

You hypothesize that converting `list2` to a `set` for O(1) lookups will be much faster. Let's patch it and find out\!

```python
# 3. Patch the function with a faster implementation
# We will replace the body of the function (lines 3 to 7)
# Note: The end line in the magic (8) is exclusive.
%%patchimport my_utility_module 3 8
    # A much faster implementation using a set for O(1) lookups.
    set2 = set(list2)
    return [item for item in list1 if item in set2]

# 4. Re-import and time the new version
import my_utility_module # This re-import loads the patched version

print("\nTiming patched (set-based) implementation:")
%timeit my_utility_module.find_common_elements(data, sample_to_find)
```

**Expected Output:**

You will see a dramatic performance improvement, proving your hypothesis in seconds.

```
Timing original (list-based) implementation:
11.5 ms ± 123 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

Patch applied from line 3 to 8:
...

REMEMBER TO DO `import my_utility_module` OR `from my_utility_module import ...` AFTER THIS MAGIC CALL!

Timing patched (set-based) implementation:
33.1 µs ± 0.2 µs per loop (mean ± std. dev. of 7 runs, 10000 loops each)
```

This workflow allows for incredibly fast, iterative performance tuning without ever leaving your notebook.

---

## ⚙️ How It Works

This magic uses Python's `importlib` library. It locates the source file for the specified module, reads its content, and applies the patch from your cell to the source code string in memory. Then, it compiles this new, modified source code and replaces the original module object in `sys.modules`. When you call `import` in the next cell, you get the patched version.

---

## ⚠️ Limitations

- **In-Memory Only**: Patches are not saved to disk and last only for the current kernel session.
- **Indentation**: You must provide the correct indentation for your patch code. There is no auto-indentation.
- **`??` Operator**: Using `??` in IPython/Jupyter to view a patched object's source may show the original, unpatched code.
- **Development Use**: This tool is designed for interactive debugging and experimentation, not for use in production code.

---

## 🤝 Contributing

Contributions are welcome! Whether it's reporting a bug, suggesting an enhancement, or submitting a pull request, your help is appreciated.

### Development Setup

1.  Fork and clone the repository.
2.  It is recommended to create a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  Install the project in editable mode along with its development dependencies:
    ```bash
    pip install -r requirements_dev.txt
    ```

### Running Tests & Linters

This project uses `tox` to automate linting and testing across multiple Python versions. It ensures code quality and compatibility.

To run the full suite of checks, simply execute:

```bash
tox
```

### Bug Reports & Feature Requests

Please use the [GitHub Issues](https://github.com/dev-random-sas/patchimport-magic/issues) to report bugs or request new features. When reporting a bug, please include:

- Your operating system and Python version.
- A minimal, reproducible example demonstrating the issue.
- The expected behavior and what actually happened.

### Pull Requests

1.  Create a new branch for your feature or bugfix.
2.  Make your changes and add or update tests as appropriate.
3.  Ensure all tests and lint checks pass by running `tox`.
4.  Submit a pull request with a clear description of your changes.

---

## 📄 License

This project is licensed under the **BSD-3-Clause License**. See the `LICENSE` file for details.
