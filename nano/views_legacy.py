"""Compatibility exports for the modular view split.

The URL package historically imported these views from ``views_legacy``.
Keep this small adapter while callers migrate to the owning modules.
"""

from .views_core import *  # noqa: F401,F403
from .views_pos import *  # noqa: F401,F403
from .views_communications import *  # noqa: F401,F403
