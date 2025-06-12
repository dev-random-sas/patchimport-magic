# patchimport-magic

IPython magic to patch modules before you import them.

`patchimport-magic` provides a cell magic (`%%patchimport`) that allows you to apply quick, in-memory patches to any installed Python module directly from a Jupyter Notebook or IPython session. This is incredibly useful for rapid debugging, experimenting with library internals without forking, or testing a potential fix on the fly.

---

## 🤔 Why?

Have you ever wanted to:

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

### Example 1: Inserting Code

Let's add a `print` statement to the standard library's `abc.py` module. The original source for the `ABC` class (around line 99) looks like this:

```python
# ...
class ABC(type):
    """Helper class that provides a standard way to create an ABC.
    ...
    """
    def __new__(mcls, name, bases, namespace, /, **kwargs):
# ...
```

We can insert a new attribute right before the class definition using the magic. Note that line numbers start at 1.

```python
# %%
%%patchimport abc 99
# This line will be inserted before line 99 of the original abc.py
data = 'SURPRISE!!!'

# %%
# Now, import the patched module and access the new data
import abc

print(abc.data)
```

**Output:**

```
Patch applied from line 99 to 99:

  96
  97 # A new abstract base class may be created by deriving from ABC.
  98 #
  99+data = 'SURPRISE!!!'
 100 class ABC(type):
 101     """Helper class that provides a standard way to create an ABC.
 102

REMEMBER TO DO `import abc` OR `from abc import ...` AFTER THIS MAGIC CALL!

SURPRISE!!!
```

### Example 2: Replacing Code

Now, let's modify the behavior of `random.choice()`. The original function simply returns a random element. We'll patch it to always return the _first_ element of a sequence.

The source for `random.choice` is around lines 376-378 in `random.py`:

```python
# original random.py
def choice(self, seq):
    """Choose a random element from a non-empty sequence."""
    return seq[self._randbelow(len(seq))]
```

We will replace the function body (line 378) with our own code. To do this, we specify a start and end line. The replacement will occur from `start_line` up to (but not including) `end_line`.

```python
# %%
# Replace lines 378 through 378 (i.e., just line 378)
%%patchimport random 378 379
        return seq[0] # Always return the first element!

# %%
import random

my_list = ['apple', 'banana', 'cherry']
print(f"Patched random.choice: {random.choice(my_list)}")
print(f"Patched random.choice: {random.choice(my_list)}")
```

**Output:**

```
Patch applied from line 378 to 379:

 375     # It is not part of the public API and may be removed at any time.
 376
 377     def choice(self, seq):
 378+        return seq[0] # Always return the first element!
 379         """Choose a random element from a non-empty sequence."""
 380         try:
 381             i = self._randbelow(len(seq))

REMEMBER TO DO `import random` OR `from random import ...` AFTER THIS MAGIC CALL!

Patched random.choice: apple
Patched random.choice: apple
```

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

## 📄 License

This project is licensed under the **BSD-3-Clause License**. See the `LICENSE` file for details.
