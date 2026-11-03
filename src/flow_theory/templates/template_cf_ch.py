"""Starter [cf_ch] section template."""


# --------------------------------------------------
# public API
# --------------------------------------------------
def render_cf_ch_section() -> str:
    """Build a starter [cf_ch] section."""

    lines = [
        "# --------------------------------------------------",
        "# skin-friction/stanton number estimates",
        "# --------------------------------------------------",
        "[cf_ch]",
        "# toggle to enable/disable this section when running flow-theory",
        "# flow conditions file path (JSON) for this section",
        'flow_conditions = "flow_conditions.json"',
        "# x input options:",
        "# - single location             : x = 1.0",
        "# - start, end, number of points: x = [0.001, 1.0, 100]",
        "# - start, end, increment       : x = [0.001, 1.0, 0.002]",
        "x = [1.0e-3, 1.0, 100]",
        '# mode: "laminar" or "turbulent" -> compute both if unset',
        'mode = ""',
        "# method: what methods are used to compute -> compute all if unset",
        '# laminar methods: "blasius", "eckert_reference", "similarity"',
        '# turbulent methods: "van_driest_ii", "spalding_chi", "sommer_short", "white_christoph"',
        'method = ""',
        '# wall type: "adiabatic" or "isothermal"',
        'wall_type = "adiabatic"',
        "# wall temperature (K) for isothermal wall condition; ignored for adiabatic wall",
        "temp_wall = 300.0",
        "# output base filename; if both modes run, writes *_laminar and *_turbulent",
        'output = "cf_vs_x.dat"',
    ]
    return "\n".join(lines)
