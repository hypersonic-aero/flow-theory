"""Reusable TOML templates for flow-theory CLI commands."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from flow_theory.templates.template_boundary_layer_thickness import (
    render_boundary_layer_thickness_section,
)
from flow_theory.templates.template_cf_ch import render_cf_ch_section
from flow_theory.templates.template_entropy_layer_estimate import (
    render_entropy_layer_estimate_section,
)
from flow_theory.templates.template_entropy_layer_swallowing import (
    render_entropy_layer_swallowing_section,
)
from flow_theory.templates.template_shock_shape import render_shock_shape_section
from flow_theory.templates.template_shock_standoff import (
    render_shock_standoff_section,
)
from flow_theory.templates.template_transition import render_transition_section

# --------------------------------------------------
# section registry
# --------------------------------------------------
SECTION_RENDERERS = {
    "boundary_layer_thickness": render_boundary_layer_thickness_section,
    "cf_ch": render_cf_ch_section,
    "entropy_layer_estimate": render_entropy_layer_estimate_section,
    "entropy_layer_swallowing": render_entropy_layer_swallowing_section,
    "shock_standoff": render_shock_standoff_section,
    "shock_shape": render_shock_shape_section,
    "transition": render_transition_section,
}


# --------------------------------------------------
# public API
# --------------------------------------------------
def render_templates(preset: str) -> str:
    """Build the starter config text for one calculator's init command.

    Args:
        preset: Registered section name (a key of SECTION_RENDERERS).

    Returns:
        Full TOML template text.
    """

    # build guidance comments
    lines = [
        "# flow-theory starter config",
        "#",
        "# edit these values, then run the calculator's scoped run command",
        "#",
        "",
    ]

    # get section renderer function from registry (defined above)
    render_section = SECTION_RENDERERS[preset]

    # append rendered section text to lines
    lines.append(render_section())

    # join lines into a single string and return (rstrip to remove trailing whitespace, then add a final newline)
    return "\n".join(lines).rstrip() + "\n"
