# Shock Shape

```python
from canonical_geometries.config import load_geometry
from flow_theory.shock import compute_shock_shape

# the body from its geometry file (`geometry cone init` writes one; grid-generator
# reads the same file); x_e lies on the body, at most at its end
geometry = load_geometry("geometry.toml")

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

::: flow_theory.geometry.body.resolve_x_e

::: flow_theory.geometry.body.build_body
