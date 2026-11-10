"""Starter [entropy_layer_swallowing] workflow template."""


def render_entropy_layer_swallowing_section() -> str:
    """Build a starter [entropy_layer_swallowing] section."""

    lines = [
        "[entropy_layer_swallowing]",
        "# mach, re1, nose_radius and tw_t0 may each be a list, swept case by case (lists",
        "# of equal length; a single number is used for every case)",
        "# Mach number",
        "mach = 8.0",
        "# unit Reynolds number [1/m]",
        "re1 = 3.0e6",
        "# nose radius [m]",
        "nose_radius = 0.0254",
        "# wall-to-stagnation temperature ratio T_w / T_0",
        "tw_t0 = 0.4",
        "# ratio of specific heats",
        "gamma = 1.4",
        "# output file (Tecplot ASCII), relative to this file",
        'output = "entropy_layer_swallowing.dat"',
    ]
    return "\n".join(lines)
