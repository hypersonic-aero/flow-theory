# Similarity Method

This method estimates skin friction directly from a Falkner-Skan similarity
solution[^falkner_skan_1931].

It uses the simbl similarity solver[^simbl_software] to obtain the wall-shear
quantity \(f''(0)\), where the normalized streamwise velocity is
\(\overline{u} = u/u_e\). Thus,

$$
f''(0) = \left.\frac{\partial \overline{u}}{\partial \eta}\right|_w,
$$

$$
\left.\frac{\partial u}{\partial \eta}\right|_w = u_e f''(0).
$$

Convert to physical wall-normal gradient using the Falkner-Skan coordinate
transformation (see
[Falkner-Skan Derivation](https://hypersonic-aero.github.io/similarity-bl/theory/falkner_skan/derivation/)):

$$
\left.\frac{\partial \eta}{\partial y}\right|_w
=
\left.\frac{\rho u_e}{\sqrt{2\xi}}\right|_w
=
\frac{\rho_w u_e}{\sqrt{2\xi}}.
$$

Here \(\xi\) is the transformed streamwise coordinate,

$$
\xi = \int_0^x \rho_e\mu_e u_e\,dx',
$$

so

$$
\left.\frac{\partial u}{\partial y}\right|_w
=
\left.\frac{\partial u}{\partial \eta}\right|_w
\left.\frac{\partial \eta}{\partial y}\right|_w
=
 f''(0)\frac{\rho_w u_e^2}{\sqrt{2\xi}}.
$$

Substitute into the skin-friction definition from the
[Skin Friction and Stanton Number overview](../cf_ch.md) to get

$$
c_f(\xi)
=
\frac{2\mu_w}{\rho_e u_e^2}\overbrace{\left.\frac{\partial u}{\partial y}\right|_w}^{f''(0)\frac{\rho_w u_e^2}{\sqrt{2\xi}}}
=
\frac{\mu_w\rho_w}{\rho_e}\,\frac{\sqrt{2}}{\sqrt{\xi}}\,f''(0).
$$

The Stanton number is computed with the Reynolds analogy:

$$
C_h = \frac{c_f}{2\,\mathrm{Pr}^{2/3}}.
$$

## Limits

### Zero Pressure Gradient Flat Plate

For a zero-pressure-gradient flat plate,

$$
\xi = \rho_e\mu_e u_e x.
$$

The edge quantities (subscript e) are freestream quantities (subscript
\(\infty\)). Therefore,

$$
\xi = \rho_\infty u_\infty \mu_\infty x.
$$

Using the unit Reynolds number,

$$
Re_1 = \frac{\rho_\infty u_\infty}{\mu_\infty},
$$

and the Reynolds number based on the streamwise coordinate,

$$
Re_x = Re_1 x,
$$

so

$$
\xi = Re_1 \mu_\infty^2 x = Re_x \mu_\infty^2.
$$

Substituting this into the expression above and recognizing
\(\rho_e = \rho_\infty\) results in

$$
c_f = \frac{\mu_w\rho_w}{\rho_\infty} \frac{\sqrt{2}}{\sqrt{Re_x \mu_\infty^2}} f''(0)
=
\frac{\mu_w\rho_w}{\mu_\infty \rho_\infty} \sqrt{\frac{2}{Re_x}} f''(0).
$$

### Circular Cone

For axisymmetric flow over a circular cone, the corresponding similarity
reduction follows through the Mangler transformation. This gives the cone
analogue of the flat-plate limit while preserving the same underlying
Falkner-Skan structure.

In this limit, the edge quantities do not reduce to freestream values.
Instead, they are the local cone-edge quantities from the Taylor-Maccoll solution:

$$
\begin{aligned}
\rho_e &= \rho_{e,\mathrm{TM}} = \text{const.}, \\
u_e &= u_{e,\mathrm{TM}} = \text{const.}, \\
\mu_e &= \mu_{e,\mathrm{TM}} = \text{const.}
\end{aligned}
$$

With \(x_\mathrm{cone}\) being the distance along the cone surface measured from
the virtual cone origin, the Mangler-equivalent flat-plate coordinate is
\(\tilde{x}_{\mathrm{cone}}\):

$$
\tilde{x}_{\mathrm{cone}}
=
\frac{1}{L^2}\int_0^{x_\mathrm{cone}} r_0(\xi)^2\,d\xi
=
\frac{\sin^2\theta_\mathrm{cone}}{3L^2}\,x_\mathrm{cone}^3.
$$

The corresponding local Reynolds number is

$$
Re_{x,\mathrm{cone}}
=
\frac{\rho_{e,\mathrm{TM}}\,u_{e,\mathrm{TM}}\,\tilde{x}_{\mathrm{cone}}}{\mu_{e,\mathrm{TM}}}.
$$

The skin-friction expression keeps the same similarity structure, with the correction due to the Mangler transform:

$$
c_{f,\mathrm{cone}}
=
\sqrt{3}\,\frac{\mu_w\rho_w}{\rho_{e,\mathrm{TM}}\,\mu_{e,\mathrm{TM}}}
\sqrt{\frac{2}{Re_{x,\mathrm{cone}}}}\,f''(0).
$$

## References

[^falkner_skan_1931]: Falkner, V.M. and Skan, S.W. (1931). Solutions of the boundary-layer equations. *Philosophical Magazine*, 12(80), 865-896.
[^simbl_software]: Hader, C. (2026). *simbl: Similarity boundary layer solver* (Version 0.2.0) [Software]. DOI: [10.5281/zenodo.20648457](https://doi.org/10.5281/zenodo.20648457). Repository: [hypersonic-aero/similarity-bl](https://github.com/hypersonic-aero/similarity-bl).
