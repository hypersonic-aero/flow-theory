"""Starter [shock_standoff] section template."""


# --------------------------------------------------
# public API
# --------------------------------------------------
def render_shock_standoff_section() -> str:
    """Build a starter [shock_standoff] section."""

    lines = [
        "# --------------------------------------------------",
        "# normal-shock standoff estimate",
        "# --------------------------------------------------",
        "[shock_standoff]",
        'flow_conditions = "flow_conditions.json"',
        '# geometry: "sphere" or "cylinder"',
        'geometry = "sphere"',
        "nose_radius = 0.01",
        '# method: "ambrosio_wortman", "ambrosio_wortman_density_ratio", or "serbin"',
        'method = "ambrosio_wortman"',
        'output = "shock_standoff.dat"',
    ]

    return "\n".join(lines)
