"""AI schema compatibility shim.

Canonical location: modules.ai_lab.schemas
"""

import sys

from modules.ai_lab import schemas as _domain_schemas

sys.modules[__name__] = _domain_schemas

