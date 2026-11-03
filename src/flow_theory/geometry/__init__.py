"""Bodies for flow-theory tools, built from canonical-geometries."""

# --------------------------------------------------
# package imports
# --------------------------------------------------
from .body import (
    BODY_GEOMETRIES,
    Body,
    arc_length_at_x,
    build_body,
    fill_geometry_extent,
    parse_geometry,
)

__all__ = [
    "BODY_GEOMETRIES",
    "Body",
    "arc_length_at_x",
    "build_body",
    "fill_geometry_extent",
    "parse_geometry",
]
