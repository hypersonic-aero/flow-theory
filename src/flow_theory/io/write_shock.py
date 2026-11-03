"""Terminal, Tecplot and CSV output for shock calculations."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from flow_theory.shock import ShockShapeResult, ShockStandoffResult

from .tecplot_ascii import TecplotFile, write_tecplot

logger = logging.getLogger("flow-theory")


# --------------------------------------------------
# shock-standoff output
# --------------------------------------------------
def write_shock_standoff(
    result: ShockStandoffResult,
    output: Path | None,
) -> None:
    """Report and optionally write a shock-standoff result."""

    # report the scalar estimate for both direct and config-driven workflows
    logger.info(
        "shock standoff: Delta=%.8e, Delta/R_nose=%.8e",
        result.delta,
        result.delta_over_radius,
    )

    # skip file output when no path is configured
    if output is None:
        logger.info("shock-standoff output file is not configured; skipping file write")
        return

    # write one complete result row
    values = np.array(
        [
            [
                result.mach,
                result.nose_radius,
                result.delta,
                result.delta_over_radius,
            ]
        ]
    )
    zone_name = f"shock standoff {result.geometry} {result.method}"
    write_tecplot(
        output,
        title="flow_theory shock standoff",
        variables=["Mach", "R_nose", "Delta", "Delta_over_R_nose"],
        zone_name=zone_name,
        values=values,
    )
    logger.info("wrote %s", output)


# --------------------------------------------------
# shock-shape output
# --------------------------------------------------
def write_shock_shape(
    result: ShockShapeResult,
    output: Path | None,
) -> None:
    """Report and optionally write a shock-shape result."""

    # report shape extent and the composed standoff estimate
    logger.info(
        "shock shape: %d points, y=[%.8e, %.8e], Delta=%.8e",
        result.x.size,
        result.y[0],
        result.y[-1],
        result.standoff.delta,
    )

    # skip file output when no path is configured
    if output is None:
        logger.info("shock-shape output file is not configured; skipping file write")
        return

    # write in the format the extension picks (Tecplot unless registered otherwise)
    write = SHOCK_SHAPE_WRITERS.get(output.suffix.lower(), _write_shock_shape_tecplot)
    write(result, output)
    logger.info("wrote %s", output)


def _write_shock_shape_tecplot(result: ShockShapeResult, output: Path) -> None:
    """Write the shock and the body as two Tecplot ASCII zones."""

    # write both sampled zones: shock locus and body surface
    shock_values = np.column_stack([result.x, result.y])
    body_values = np.column_stack([result.body_x, result.body_y])
    shock_zone_name = f"shock shape {result.geometry} {result.method}"
    body_zone_name = f"body surface {result.geometry}"

    # write both zones with one shared variable list
    with TecplotFile(output, title="flow_theory shock shape", variables=["x", "y"]) as tecplot:
        tecplot.write_zone(shock_zone_name, shock_values)
        tecplot.write_zone(body_zone_name, body_values)


def _write_shock_shape_csv(result: ShockShapeResult, output: Path) -> None:
    """Write the shock alone as x, y columns with a header (e.g. for grid-generator)."""

    # one row per shock point
    values = np.column_stack([result.x, result.y])
    np.savetxt(output, values, delimiter=",", header="x,y", comments="", fmt="%.16e")


# shock-shape writers by file extension; other extensions get Tecplot ASCII
SHOCK_SHAPE_WRITERS = {
    ".csv": _write_shock_shape_csv,
}
