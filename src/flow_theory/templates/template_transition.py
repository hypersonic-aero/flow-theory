"""Starter [transition] workflow template."""


# --------------------------------------------------
# public API
# --------------------------------------------------
def render_transition_section() -> str:
    """Build a starter [transition] section."""

    # build the editable transition example
    lines = [
        "[transition]",
        "# mach, re1 and tw_te may each be a list, swept case by case (lists of equal",
        "# length; a single number is used for every case)",
        "# edge Mach number",
        "mach = 5.0",
        "# unit Reynolds number [1/m]",
        "re1 = 3.0e6",
        "# wall-to-edge temperature ratio T_w / T_e",
        "tw_te = 0.5",
        '# transition-onset criterion: "van_driest_blumer"',
        'method = "van_driest_blumer"',
        "# output file (Tecplot ASCII), relative to this file",
        'output = "transition.dat"',
    ]

    # join the section into TOML text
    content = "\n".join(lines)
    return content
