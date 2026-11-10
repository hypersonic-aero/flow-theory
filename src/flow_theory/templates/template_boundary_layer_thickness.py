"""Starter [boundary_layer_thickness] workflow template."""


def render_boundary_layer_thickness_section() -> str:
    """Build a starter [boundary_layer_thickness] section."""

    lines = [
        "[boundary_layer_thickness]",
        "# x, re1, mach and tw_t0 may each be a list, swept case by case (lists of equal",
        "# length; a single number is used for every case)",
        "# streamwise stations x [m], measured from the leading edge",
        "x = [0.1, 0.5, 1.0]",
        "# unit Reynolds number [1/m]",
        "re1 = 3.0e6",
        '# method: "blasius" (incompressible) or "eckert_reference" (compressible, through',
        "# Eckert's reference temperature; needs mach and tw_t0)",
        'method = "eckert_reference"',
        "# edge Mach number (eckert_reference only)",
        "mach = 8.0",
        "# wall-to-stagnation temperature ratio T_w / T_0 (eckert_reference only)",
        "tw_t0 = 0.4",
        "# ratio of specific heats",
        "gamma = 1.4",
        "# output file (Tecplot ASCII), relative to this file",
        'output = "boundary_layer_thickness.dat"',
    ]
    return "\n".join(lines)
