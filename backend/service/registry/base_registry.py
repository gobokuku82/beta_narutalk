"""
Base Registry
모든 레지스트리의 기본 클래스
"""

import logging
from typing import Dict, Any, Optional, Type, Callable, List
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


logger = logging.getLogger(__name__)


class RegistryError(Exception):
    """Registry related errors"""
    pass


@dataclass
class RegistryEntry:
    """레지스트리 항목"""
    name: str
    item: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"


class BaseRegistry(ABC):
    """
    Base Registry Class
    모든 레지스트리의 기본 클래스
    """

    def __init__(self, name: str = "BaseRegistry"):
        """
        Initialize registry

        Args:
            name: Registry name
        """
        self._name = name
        self._items: Dict[str, RegistryEntry] = {}
        self._logger = logging.getLogger(f"{__name__}.{name}")
        self._logger.info(f"Initializing {name}")

    @property
    def name(self) -> str:
        """Get registry name"""
        return self._name

    def register(
        self,
        name: str,
        item: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        version: str = "1.0.0",
        override: bool = False
    ) -> None:
        """
        Register an item

        Args:
            name: Unique identifier
            item: Item to register
            metadata: Additional metadata
            tags: Tags for categorization
            version: Version string
            override: Whether to override existing item

        Raises:
            RegistryError: If name already exists and override is False
        """
        if name in self._items and not override:
            raise RegistryError(
                f"Item '{name}' already registered in {self._name}. "
                f"Use override=True to replace."
            )

        entry = RegistryEntry(
            name=name,
            item=item,
            metadata=metadata or {},
            tags=tags or [],
            version=version
        )

        self._items[name] = entry
        action = "Overridden" if name in self._items else "Registered"
        self._logger.info(f"{action} '{name}' (version {version}) in {self._name}")

    def unregister(self, name: str) -> None:
        """
        Unregister an item

        Args:
            name: Item name to unregister

        Raises:
            RegistryError: If item not found
        """
        if name not in self._items:
            raise RegistryError(f"Item '{name}' not found in {self._name}")

        del self._items[name]
        self._logger.info(f"Unregistered '{name}' from {self._name}")

    def get(self, name: str, default: Any = None) -> Any:
        """
        Get registered item

        Args:
            name: Item name
            default: Default value if not found

        Returns:
            Registered item or default
        """
        entry = self._items.get(name)
        if entry is None:
            if default is None:
                self._logger.warning(f"Item '{name}' not found in {self._name}")
            return default
        return entry.item

    def get_entry(self, name: str) -> Optional[RegistryEntry]:
        """
        Get registry entry (with metadata)

        Args:
            name: Item name

        Returns:
            Registry entry or None
        """
        return self._items.get(name)

    def has(self, name: str) -> bool:
        """
        Check if item exists

        Args:
            name: Item name

        Returns:
            True if exists
        """
        return name in self._items

    def list_all(self) -> List[str]:
        """
        List all registered item names

        Returns:
            List of item names
        """
        return list(self._items.keys())

    def list_by_tag(self, tag: str) -> List[str]:
        """
        List items by tag

        Args:
            tag: Tag to filter by

        Returns:
            List of item names with the tag
        """
        return [
            name for name, entry in self._items.items()
            if tag in entry.tags
        ]

    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an item

        Args:
            name: Item name

        Returns:
            Metadata dictionary or None
        """
        entry = self._items.get(name)
        return entry.metadata if entry else None

    def get_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get complete info about an item

        Args:
            name: Item name

        Returns:
            Info dictionary or None
        """
        entry = self._items.get(name)
        if not entry:
            return None

        return {
            "name": entry.name,
            "metadata": entry.metadata,
            "tags": entry.tags,
            "version": entry.version,
            "registered_at": entry.registered_at
        }

    def clear(self) -> None:
        """Clear all registered items"""
        count = len(self._items)
        self._items.clear()
        self._logger.info(f"Cleared {count} items from {self._name}")

    def count(self) -> int:
        """
        Get count of registered items

        Returns:
            Number of items
        """
        return len(self._items)

    def search(self, query: str) -> List[str]:
        """
        Search items by name or metadata

        Args:
            query: Search query

        Returns:
            List of matching item names
        """
        query_lower = query.lower()
        results = []

        for name, entry in self._items.items():
            # Search in name
            if query_lower in name.lower():
                results.append(name)
                continue

            # Search in tags
            if any(query_lower in tag.lower() for tag in entry.tags):
                results.append(name)
                continue

            # Search in metadata
            metadata_str = str(entry.metadata).lower()
            if query_lower in metadata_str:
                results.append(name)

        return results

    def export(self) -> Dict[str, Any]:
        """
        Export registry state

        Returns:
            Registry state as dictionary
        """
        return {
            "name": self._name,
            "count": len(self._items),
            "items": {
                name: {
                    "metadata": entry.metadata,
                    "tags": entry.tags,
                    "version": entry.version,
                    "registered_at": entry.registered_at
                }
                for name, entry in self._items.items()
            }
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self._name}', items={len(self._items)})"

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, name: str) -> bool:
        return name in self._items

    def __iter__(self):
        return iter(self._items.keys())
