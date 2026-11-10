"""Starter [entropy_layer_estimate] workflow template."""


def render_entropy_layer_estimate_section() -> str:
    """Build a starter [entropy_layer_estimate] section."""

    lines = [
        "[entropy_layer_estimate]",
        "# x, mach and nose_radius may each be a list, swept case by case (lists of equal",
        "# length; a single number is used for every case)",
        "# streamwise station x [m], measured from the nose",
        "x = 0.1",
        "# Mach number",
        "mach = 8.0",
        "# nose radius [m]",
        "nose_radius = 0.0254",
        "# ratio of specific heats",
        "gamma = 1.4",
        "# output file (Tecplot ASCII), relative to this file",
        'output = "entropy_layer_estimate.dat"',
    ]
    return "\n".join(lines)
