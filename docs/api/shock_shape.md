# Shock Shape

```python
from flow_theory.geometry import parse_geometry
from flow_theory.shock import compute_shock_shape

# the body ends at x_e, so its [geometry] table has no length
geometry = parse_geometry(
	{"type": "cone", "nose_radius": 0.01, "half_angle": 7.0},
	x_e=0.10,
)

result = compute_shock_shape(
	mach=6.0,
	gamma=1.4,
	geometry=geometry,
	x_e=0.10,
	n_points=201,
)
```

::: flow_theory.shock.shape.ShockShapeResult

::: flow_theory.shock.shape.compute_shock_shape

::: flow_theory.geometry.body.parse_geometry

::: flow_theory.geometry.body.build_body
