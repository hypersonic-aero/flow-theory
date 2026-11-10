"""Starter [shock_shape] section template."""


# --------------------------------------------------
# public API
# --------------------------------------------------
def render_shock_shape_section() -> str:
    """Build a starter [shock_shape] section."""

    lines = [
        "# --------------------------------------------------",
        "# detached bow-shock locus",
        "# --------------------------------------------------",
        "[shock_shape]",
        "# flow conditions for the shock shape estimation (flow-state JSON with the freestream)",
        "# (relative to this file)",
        'flow_conditions = "flow_conditions.json"',
        "# method: billig, or billig_blended (wedge, cone, tangent ogive: Billig at the",
        "# nose, the sharp body's shock from its virtual origin downstream, computed by",
        "# the method of characteristics)",
        'method = "billig"',
        "# billig_blended only: blend length in nose radii (default 35)",
        "# blend_nose_radii = 35.0",
        "# n_points: points on the shock and on the body (spread evenly in arc length",
        "# and turning angle, so the nose and the shock vertex are resolved)",
        "n_points = 201",
        "# optional: streamwise end of the shock [m], measured from the nose tip; at most",
        "# the body's end (left out: the body's end)",
        "# x_e = 0.10",
        '# .csv: the shock as x, y columns; output = "shock_shape.csv" is the curve',
        "# grid-generator's shock-aligned template reads by default ([shock] curve)",
        "# any other extension: Tecplot ASCII with a shock zone and a body zone",
        "# (relative to this file)",
        'output = "shock_shape.dat"',
        "",
        "# the body: a geometry file (canonical-geometries' geometry.toml, which",
        "# `geometry <type> init` writes: plate, wedge, cone, tangent-ogive); grid-generator",
        "# reads the same file, so the body is defined once. For a quick estimate without",
        "# a geometry file, give the body's keys here instead of file: the same keys as",
        "# geometry.toml's [geometry] table, length included (e.g. type, nose_radius,",
        "# length, half_angle)",
        "[shock_shape.geometry]",
        "# geometry file, relative to this file",
        'file = "geometry.toml"',
    ]

    return "\n".join(lines)
