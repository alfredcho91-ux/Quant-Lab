"""
Backend package initialization.
Sets up Python path to allow imports from project root (core/).
This eliminates the need for sys.path.insert in individual files.
"""
import sys
from pathlib import Path

# Add project root to Python path (for importing core modules)
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
