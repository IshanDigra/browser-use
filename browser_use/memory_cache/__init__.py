"""Records every action the agent executes so a deterministic automation can be derived from it."""

from browser_use.memory_cache.choke import cached_execute_action
from browser_use.memory_cache.models import CachedStep

__all__ = ['CachedStep', 'cached_execute_action']
