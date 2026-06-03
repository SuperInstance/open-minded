"""Ensure the local interpreter/ package takes priority over pip-installed open-interpreter."""
import sys
import os

# Prepend the project root so local interpreter/ wins over pip-installed
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Purge any cached interpreter modules from site-packages
for key in list(sys.modules):
    if key == "interpreter" or key.startswith("interpreter."):
        del sys.modules[key]
