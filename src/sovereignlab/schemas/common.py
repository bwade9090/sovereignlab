"""Shared strict types for versioned public data contracts."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

SCHEMA_VERSION = "1.0.0"

Identifier = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=128,
        pattern=r"^[a-z0-9][a-z0-9._-]*[a-z0-9]$",
    ),
]
NonEmptyText = Annotated[str, StringConstraints(min_length=1, max_length=10_000)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
MediaType = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*$"),
]


class StrictModel(BaseModel):
    """Immutable model that rejects undeclared input fields."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )
