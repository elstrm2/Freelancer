# only for python < 3.11

import os
import sys

# Define the directory where pymorphy2 is installed
# Adjust the path if necessary
pymorphy2_dir = os.path.join(sys.prefix, "Lib", "site-packages", "pymorphy2")

# Define the file and function we want to patch
file_to_patch = os.path.join(pymorphy2_dir, "units", "base.py")
old_function = "getargspec"
new_function = "getfullargspec"


def patch_file(file_path, old_func, new_func):
    """Patches a file by replacing the old function with the new one."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Check if the patch is necessary
        if old_func in content:
            content = content.replace(old_func, new_func)

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)

            print(
                f"Successfully patched {file_path}: replaced '{old_func}' with '{new_func}'."
            )
        else:
            print(f"No patch needed in {file_path}. '{old_func}' not found.")

    except Exception as e:
        print(f"Error patching file {file_path}: {e}")


if __name__ == "__main__":
    # Check if pymorphy2 is installed
    if os.path.exists(file_to_patch):
        patch_file(file_to_patch, old_function, new_function)
    else:
        print("pymorphy2 is not installed or path is incorrect.")
