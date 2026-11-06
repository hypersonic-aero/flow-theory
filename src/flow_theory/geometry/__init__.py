"""Bodies for flow-theory tools, built from canonical-geometries."""

# --------------------------------------------------
# package imports
# --------------------------------------------------
from .body import (
    BODY_GEOMETRIES,
    Body,
    arc_length_at_x,
    body_end,
    build_body,
    parse_geometry,
    resolve_x_e,
)

__all__ = [
    "BODY_GEOMETRIES",
    "Body",
    "arc_length_at_x",
    "body_end",
    "build_body",
    "parse_geometry",
    "resolve_x_e",
]
