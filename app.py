import os
import sys

# Ensure local pdf2zh module is prioritized
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf2zh.gui import setup_gui

if __name__ == "__main__":
    setup_gui()
