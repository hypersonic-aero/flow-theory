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
        "# streamwise end [m], measured from the nose tip; the body ends here too",
        "x_e = 0.10",
        "# .csv: the shock as x, y columns (e.g. for grid-generator)",
        "# any other extension: Tecplot ASCII with a shock zone and a body zone",
        'output = "shock_shape.dat"',
        "",
        "# body: canonical-geometries' [geometry] table, without its extent (x_e sets it)",
        "# types: plate, wedge (planar), cone, tangent-ogive (axisymmetric)",
        "[shock_shape.geometry]",
        "# geometry type (plate, wedge, cone, tangent-ogive)",
        'type = "cone"',
        "# nose radius [m]",
        "nose_radius = 0.01",
        "# half_angle [deg]: cone and wedge (0 for a sphere-cylinder)",
        "half_angle = 7.0",
        "",
        "# a tangent ogive instead (a cylinder follows when x_e lies past the base):",
        "# geometry type",
        '# type = "tangent-ogive"',
        "# nose radius [m]",
        "# nose_radius = 0.001",
        "# sharp-ogive length, tip to base [m]",
        "# length = 0.5",
        "# base radius [m]",
        "# base_radius = 0.05",
    ]

    return "\n".join(lines)
