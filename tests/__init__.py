<<<<<<< HEAD
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import smd


def empty_dir(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for f in files:
            os.remove(os.path.join(root, f))
        for d in dirs:
            os.rmdir(os.path.join(root, d))
=======
# -*- coding: utf-8 -*-
'''
.. module:: tests

Tests for the ``smd`` application.

'''


# import os
# import sys

# sys.path.insert(0, os.path.abspath(
#     os.path.join(os.path.dirname(__file__), '..')))
# import smd
>>>>>>> 1.6.0
