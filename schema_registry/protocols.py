from typing import Protocol, runtime_checkable


@runtime_checkable
class SchemaProvider(Protocol):
    """Narrow interface for schema access (Interface Segregation).

    Nodes depend on this protocol, not on SchemaRegistry directly.
    Any class with these two methods satisfies the contract.
    """

    def get_full_schema(self) -> str:
        """Returns the full schema context as a formatted string."""
        ...

    def get_schema_for_question(self, question: str) -> str:
        """Returns the schema context relevant to a specific question."""
        ...
