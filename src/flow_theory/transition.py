"""Boundary-layer transition onset, N-factor, and intermittency estimates

Provides simplified engineering correlations for laminar-to-turbulent
transition on flat plates and slender cones.  These are lightweight,
closed-form estimates intended for quick engineering screening -- rigorous
linear stability theory (LST) analysis of specific disturbance modes belongs
in `lst-tools`, and detecting transition in an existing CFD solution (a
post-processing diagnostic, e.g. from cf/ch spikes) is out of scope here
entirely; every function in this module is a predictive
correlation built from literature, not a diagnostic.

Design
------
Primary references consulted (see `references/` and the docstrings below
for exact citations):

- Van Driest & Blumer (1963): Re_theta transition-onset criterion, showing
  transition is delayed (higher Re_theta) by wall cooling and increases with
  edge Mach number.
- Mack (1975): the e^N linear-stability framework for transition
  amplification.  The exact amplification-rate integration requires solving
  the compressible stability (Orr-Sommerfeld-type) eigenvalue problem, which
  is out of scope for this closed-form correlation module -- `n_factor`
  below is a simplified engineering approximation of the qualitative trends
  (amplification grows with Reynolds number and disturbance frequency,
  and is stabilized by compressibility), not a literal digitization of
  Mack's stability charts.
- Dhawan & Narasimha (1958): universal intermittency distribution for the
  transition zone.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import numpy as np

# --------------------------------------------------
# module constants
# --------------------------------------------------

# incompressible, adiabatic-wall baseline Re_theta at transition onset for a
# low-disturbance environment (Van Driest & Blumer 1963, low-Mach limit)
_RE_THETA_BASELINE = 200.0

# Blasius momentum-thickness constant: theta/x = _BLASIUS_THETA_C/sqrt(re_x)
_BLASIUS_THETA_C = 0.664

# Dhawan-Narasimha (1958) universal intermittency shape constant
_DHAWAN_NARASIMHA_C = 0.412

# scaling of the Dhawan-Narasimha similarity variable so that gamma=0.99 at
# x_complete (see intermittency() docstring for the derivation)
_XI_AT_COMPLETE = 3.34

# Sutherland-law reference temperature for air, in degrees Rankine
# (110.4 K == 198.6 R), as used throughout the Deem & Murphy (1965)
# empirical correlation below
_SUTHERLAND_T_RANKINE = 198.6

# unit conversions used by the Deem & Murphy (1965) correlation, which is
# defined in English units (inches, degrees Rankine) -- see
# Delta_Transition_Prediction.m
_METERS_TO_INCHES = 39.3701
_KELVIN_TO_RANKINE = 1.8

# default initial guesses and convergence criteria for the bluntness-region
# iteration in transition_blunt_delta_wing (Delta_Transition_Prediction.m)
_B1_GUESS0_IN = 0.001
_B2_GUESS0_IN = 1.0
_BLUNTNESS_TOL_IN = 1.0e-5
_BLUNTNESS_MAX_ITER = 500

# sweep angle [deg] above which the Deem & Murphy correlation drops the
# bluntness dependence entirely (Delta_Transition_Prediction.m region 3, high
# sweep)
_HIGH_SWEEP_DEG = 25.0


# --------------------------------------------------
# internal helpers for transition_blunt_delta_wing (not part of the public
# API) -- ported line-by-line from Delta_Transition_Prediction.m, which
# implements the semi-empirical Deem & Murphy (1965) swept flat-plate
# transition method described by Hopkins, Jillie & Sorensen (1970)
# --------------------------------------------------
def _bluntness_reduced_mach(mach: float, sweep_deg: float) -> float:
    """Inviscid bluntness-reduced Mach number Mn at a swept leading edge.

    References:
        Deem & Murphy (1965), "Flat plate boundary-layer transition at
        hypersonic speeds", AIAA Paper 65-128 (as coded in
        Delta_Transition_Prediction.m).
    """

    # convert sweep angle to radians for the trig terms below
    cos_sweep = np.cos(np.radians(sweep_deg))

    # build the two bracketed terms from the empirical Mn relation
    term_a = 6.0 / (7.0 * mach**2 * cos_sweep**2 - 1.0)
    term_b = (6.0 * mach**2 * cos_sweep**2 * (mach**2 + 5.0)) / (
        5.0 * (mach**2 * cos_sweep**2 + 5.0)
    )

    # combine and invert to obtain Mn
    inner = 5.0 * term_a ** (5.0 / 2.0) * term_b ** (7.0 / 2.0)
    return np.sqrt(np.abs(inner ** (2.0 / 7.0) - 5.0))


def _b1_bluntness_criterion(
    Tw: float, T: float, mach: float, Rt: float, Re_per_in: float, ycdelt: float
) -> float:
    """Bluntness criterion b1 [in] separating regions 1 and 2.

    Args:
        Tw: Wall temperature [R].
        T: Freestream static temperature [R].
        mach: Freestream Mach number.
        Rt: Current transition Reynolds number estimate.
        Re_per_in: Freestream unit Reynolds number [1/in].
        ycdelt: Yc/delta ratio at the start of transition (Deem & Murphy
            Fig. 7).
    """

    # compute the Mach/wall-temperature group common to both branches below
    F = (1.73 * Tw) / (mach**2 * T) + 0.1328 + 4.27 / mach**2

    # select the Sutherland-viscosity or linear-viscosity branch depending on
    # whether the static temperature is above or below 200 R (Delta_Transition_
    # Prediction.m calculate_b11/calculate_b12)
    if T > 200.0 and Tw > 200.0:
        visc_ratio = np.sqrt((Tw / T) ** 0.5 * ((T + _SUTHERLAND_T_RANKINE) / (Tw + _SUTHERLAND_T_RANKINE)))
    elif Tw > 200.0 and T <= 200.0:
        visc_ratio = np.sqrt((T / Tw) * (Tw**1.5 / (0.03665 * T * (Tw + _SUTHERLAND_T_RANKINE))))
    else:
        raise ValueError("no empirical equation for T/Tw combination (both must exceed 200 R, or Tw>200>=T)")

    # return b1 [in] from the Deem & Murphy region 1/2 boundary relation
    return (2.545 / 3.0) * (1.0 - ycdelt) * F * mach**2 * visc_ratio * (np.sqrt(Rt) / Re_per_in)


def _b2_bluntness_criterion(
    Tw: float, Tn: float, Mn: float, Rt: float, Re_per_in: float, Rin_ratio: float
) -> float:
    """Bluntness criterion b2 [in] separating regions 2 and 3.

    Args:
        Tw: Wall temperature [R].
        Tn: Static temperature based on the bluntness-reduced Mach number [R].
        Mn: Bluntness-reduced Mach number.
        Rt: Current transition Reynolds number estimate.
        Re_per_in: Freestream unit Reynolds number [1/in].
        Rin_ratio: Inviscid surface-to-freestream Reynolds number ratio.
    """

    # compute the Mach/wall-temperature group common to both branches below
    F = (1.73 * Tw) / (Mn**2 * Tn) + 0.1328 + 4.27 / Mn**2

    # select the Sutherland-viscosity or linear-viscosity branch depending on
    # whether Tn is above or below 200 R (Delta_Transition_Prediction.m
    # calculate_b21/calculate_b22)
    if Tw > 200.0 and Tn > 200.0:
        visc_ratio = np.sqrt((Tw / Tn) ** 0.5 * ((Tn + _SUTHERLAND_T_RANKINE) / (Tw + _SUTHERLAND_T_RANKINE)))
    elif Tw > 200.0 and Tn <= 200.0:
        visc_ratio = np.sqrt((Tn / Tw) * (Tw**1.5 / (0.03665 * Tn * (Tw + _SUTHERLAND_T_RANKINE))))
    else:
        raise ValueError("no empirical equation for Tn/Tw combination (both must exceed 200 R, or Tw>200>=Tn)")

    # return b2 [in] from the Deem & Murphy region 2/3 boundary relation
    return (
        2.545
        * F
        * Mn**2
        * visc_ratio
        * (np.sqrt(Rt * Rin_ratio) / (Re_per_in * Rin_ratio))
    )


def _mach_group(M: float) -> float:
    """Mach-number amplification group used in every C1 correlation branch."""

    # this is the (R + 0.36e6*|M-3|^1.5) term repeated in each region below
    return 1.0e6 + 0.36e6 * np.abs(M - 3.0) ** 1.5


def _transition_reynolds_region1(
    mach: float, Mn: float, sweep_deg: float, b_in: float, b1_guess: float, Rin_ratio: float, Re_per_in: float
) -> float:
    """Transition Reynolds number Rt for region 1 (b < b1, any sweep)."""

    # compute the C1 correlating variable for region 1
    cos_sweep = np.cos(np.radians(sweep_deg))
    C1 = (
        np.log10(
            _mach_group(mach)
            * cos_sweep**0.5
            * (
                1.0
                + (1.0 / Rin_ratio) * (b_in / b1_guess) * (_mach_group(Mn) / _mach_group(mach) - (b_in / b1_guess))
            )
        )
        - 2.19
    )
    # convert C1 to the transition Reynolds number at the freestream unit Re
    return 10.0 ** (C1 + 0.4 * np.log10(Re_per_in))


def _transition_reynolds_region2(
    mach: float,
    Mn: float,
    sweep_deg: float,
    b_in: float,
    b1_guess: float,
    b2_guess: float,
    Rin_ratio: float,
    Re_per_in: float,
) -> float:
    """Transition Reynolds number Rt for region 2 (b1 <= b <= b2, low sweep)."""

    # compute the C1 correlating variable for region 2
    cos_sweep = np.cos(np.radians(sweep_deg))
    frac = (b_in - b1_guess) / (b2_guess - b1_guess)
    C1 = (
        np.log10(
            _mach_group(Mn) * cos_sweep**0.5 * (1.0 / Rin_ratio) * (1.0 + frac * (_mach_group(mach) / _mach_group(Mn) - frac))
        )
        - 2.19
    )
    # convert C1 to the transition Reynolds number at the freestream unit Re
    return 10.0 ** (C1 + 0.4 * np.log10(Re_per_in))


def _transition_reynolds_region3_low_sweep(mach: float, sweep_deg: float, Rin_ratio: float, Re_per_in: float) -> float:
    """Transition Reynolds number Rt for region 3, low sweep (b > b2)."""

    # compute the C1 correlating variable (bluntness dependence saturated)
    cos_sweep = np.cos(np.radians(sweep_deg))
    C1 = np.log10(_mach_group(mach) * cos_sweep**0.5 * (1.0 / Rin_ratio)) - 2.19
    return 10.0 ** (C1 + 0.4 * np.log10(Re_per_in))


def _transition_reynolds_region3_high_sweep(mach: float, sweep_deg: float, Re_per_in: float) -> float:
    """Transition Reynolds number Rt for region 3, high sweep (b > b1)."""

    # compute the C1 correlating variable (no bluntness or Mn dependence at
    # high sweep)
    cos_sweep = np.cos(np.radians(sweep_deg))
    C1 = np.log10(_mach_group(mach) * cos_sweep**0.5) - 2.19
    return 10.0 ** (C1 + 0.4 * np.log10(Re_per_in))


# --------------------------------------------------
# public API
# --------------------------------------------------
def re_theta_onset(mach: float, tw_te: float) -> float:
    """Re_theta at transition onset (Van Driest-Blumer criterion).

    Simplified engineering correlation capturing the two qualitative trends
    reported by Van Driest & Blumer (1963): transition Re_theta increases
    with edge Mach number and increases (transition delayed) with wall
    cooling (tw_te < 1).

    Args:
        mach: Edge Mach number.
        tw_te: Wall-to-edge temperature ratio.

    Returns:
        Re_theta at transition onset.

    References:
        Van Driest & Blumer (1963), "Boundary layer transition: freestream
        turbulence and pressure gradient effects", AIAA J., 1(6), 1303-1306.
    """

    # compressibility factor: transition delayed (higher Re_theta) at higher mach
    F_mach = 1.0 + 0.10 * mach**2

    # wall-cooling factor: cooling (tw_te < 1) stabilizes and delays transition
    F_wall = 1.0 / tw_te

    # return baseline Re_theta scaled by both factors
    return _RE_THETA_BASELINE * F_mach * F_wall


def transition_x(re1: float, mach: float, tw_te: float, method: str = "van_driest_blumer") -> float:
    """Transition x from unit Reynolds number and edge conditions.

    Maps the Re_theta transition-onset criterion to a streamwise location
    using the Blasius laminar momentum-thickness relation
    theta/x = 0.664/sqrt(re_x), giving Re_theta = 0.664*sqrt(re_x).

    Args:
        re1: Unit Reynolds number [1/m].
        mach: Edge Mach number.
        tw_te: Wall-to-edge temperature ratio.
        method: Transition-onset criterion to use. Only "van_driest_blumer"
            is currently implemented.

    Returns:
        x_transition: Transition location [m].

    References:
        Van Driest & Blumer (1963), "Boundary layer transition: freestream
        turbulence and pressure gradient effects", AIAA J., 1(6), 1303-1306.
    """

    # validate method selection
    if method != "van_driest_blumer":
        raise ValueError(f"method must be 'van_driest_blumer': got {method!r}")

    # compute Re_theta at onset, then invert the Blasius momentum-thickness
    # relation Re_theta = 0.664*sqrt(re_x) to find re_x, then x = re_x/re1
    Re_theta_tr = re_theta_onset(mach, tw_te)
    Re_x_tr = (Re_theta_tr / _BLASIUS_THETA_C) ** 2
    return Re_x_tr / re1


def n_factor(f: float, re_x: float, mach: float) -> float:
    """N-factor estimate (Mack e^N method).

    Simplified closed-form approximation of the e^N amplification-factor
    trend: amplification grows with the nondimensional frequency f and local
    Reynolds number re_x, and is stabilized (reduced) by compressibility, in
    line with the general behavior reported by Mack (1975) for first-mode
    instabilities.  Not a literal digitization of Mack's stability charts,
    which require solving the compressible stability eigenvalue problem
    (see `lst-tools` for a full linear stability workflow).

    Args:
        f: Nondimensional disturbance frequency, f = 2*pi*freq*nu_e/Ue^2.
        re_x: Local Reynolds number based on x.
        mach: Edge Mach number.

    Returns:
        N-factor estimate (dimensionless amplification exponent), clipped
        to be non-negative.

    References:
        Mack, L.M. (1975), "Linear stability theory and the problem of
        supersonic boundary-layer transition", AIAA J., 13(3), 278-289.
    """

    # compute the compressible stabilization factor (first-mode stabilization
    # with increasing Mach number)
    F_mach = 1.0 + 0.10 * mach**2

    # compute the amplification estimate and clip to non-negative
    N = 2.0 * np.sqrt(f * re_x) / F_mach
    return max(N, 0.0)


def intermittency(x: float, x_onset: float, x_complete: float) -> float:
    """Dhawan-Narasimha intermittency gamma(x) in [0, 1].

    Uses the universal intermittency distribution gamma = 1 - exp(-0.412*xi^2)
    with xi the Dhawan-Narasimha similarity variable, scaled here so that
    xi=0 at x_onset and xi=3.34 at x_complete (gamma=0.99, i.e. transition
    considered "complete").

    Args:
        x: Streamwise location [m].
        x_onset: Transition onset location [m].
        x_complete: Transition-complete location [m].

    Returns:
        gamma: Intermittency factor in [0, 1] (0 = fully laminar,
        1 = fully turbulent).

    References:
        Dhawan & Narasimha (1958), "Some properties of boundary layer flow
        during the transition from laminar to turbulent motion",
        J. Fluid Mech., 3(4), 418-436.
    """

    # validate transition zone ordering
    if x_complete <= x_onset:
        raise ValueError("x_complete must be greater than x_onset")

    # return zero intermittency upstream of transition onset
    if x <= x_onset:
        return 0.0

    # compute the similarity variable, scaled so xi=3.34 (gamma=0.99) at x_complete
    xi = _XI_AT_COMPLETE * (x - x_onset) / (x_complete - x_onset)

    # evaluate the Dhawan-Narasimha universal intermittency distribution
    gamma = 1.0 - np.exp(-_DHAWAN_NARASIMHA_C * xi**2)
    return min(gamma, 1.0)


def transition_blunt_delta_wing(
    mach: float,
    gamma: float,
    sweep_deg: float,
    b_nose: float,
    re1: float,
    T0: float,
    Tw: float,
    ycdelt: float = 0.8,
) -> float:
    """Transition location on a swept, blunt leading edge (delta wing).

    Direct port of `references/Delta_Transition_Prediction.m`, which
    implements the semi-empirical Deem & Murphy (1965) method for flat
    plates with supersonic, swept, blunt leading edges (the same method
    underlying the Hopkins, Jillie & Sorensen (1970) transition charts).
    The leading-edge bluntness b is classified into one of three regions
    (sharp, intermediate, or fully blunt) relative to two bluntness
    criteria b1 and b2, which are themselves functions of the transition
    Reynolds number Rt -- so b1, b2, and Rt are solved iteratively until
    self-consistent.

    Args:
        mach: Freestream Mach number.
        gamma: Specific heat ratio (used only for the static-temperature
            relation; the Deem & Murphy correlation itself is for air).
        sweep_deg: Leading-edge sweepback angle [deg].
        b_nose: Leading-edge bluntness (diameter) [m].
        re1: Freestream unit Reynolds number [1/m].
        T0: Freestream stagnation temperature [K].
        Tw: Wall temperature [K].
        ycdelt: Yc/delta ratio at the start of transition (Deem & Murphy
            Fig. 7); 0.8 is a reasonable estimate near mach=6 (see
            Delta_Transition_Prediction.m).

    Returns:
        x_t: Streamwise distance from the leading edge to transition [m].

    References:
        Deem, R.E. & Murphy, J.S. (1965), "Flat plate boundary-layer
        transition at hypersonic speeds", AIAA Paper 65-128.
        Hopkins, E.J., Jillie, D.W. & Sorensen, V.L. (1970), "Charts for
        estimating boundary-layer transition on flat plates", NASA TN
        D-5846.
    """

    # convert inputs from SI to the English/Rankine unit system used by the
    # Deem & Murphy correlation (see Delta_Transition_Prediction.m)
    b_in = b_nose * _METERS_TO_INCHES
    Re_per_in = re1 / _METERS_TO_INCHES
    T0_R = T0 * _KELVIN_TO_RANKINE
    Tw_R = Tw * _KELVIN_TO_RANKINE

    # compute freestream static temperature from stagnation temperature
    T_R = T0_R / (1.0 + 0.5 * (gamma - 1.0) * mach**2)

    # compute bluntness-reduced Mach number and its associated static
    # temperature and inviscid Reynolds number ratio
    Mn = _bluntness_reduced_mach(mach, sweep_deg)
    Tn_R = T0_R / (1.0 + 0.2 * Mn**2)
    Rin_ratio = (
        ((1.0 + 0.2 * Mn**2) / (1.0 + 0.2 * mach**2)) ** 2
        * (Mn / mach)
        * (
            (T0_R / (1.0 + 0.2 * Mn**2) + _SUTHERLAND_T_RANKINE)
            / (T0_R / (1.0 + 0.2 * mach**2) + _SUTHERLAND_T_RANKINE)
        )
    )

    # initialize the bluntness-region guesses and iterate to self-consistency
    b1_guess = _B1_GUESS0_IN
    b2_guess = _B2_GUESS0_IN
    for _ in range(_BLUNTNESS_MAX_ITER):
        # classify the current leading edge into a bluntness/sweep region
        # and evaluate the transition Reynolds number for that region
        if b_in < b1_guess:
            Rt = _transition_reynolds_region1(mach, Mn, sweep_deg, b_in, b1_guess, Rin_ratio, Re_per_in)
        elif b1_guess <= b_in <= b2_guess and sweep_deg <= _HIGH_SWEEP_DEG:
            Rt = _transition_reynolds_region2(mach, Mn, sweep_deg, b_in, b1_guess, b2_guess, Rin_ratio, Re_per_in)
        elif b_in >= b2_guess and sweep_deg <= _HIGH_SWEEP_DEG:
            Rt = _transition_reynolds_region3_low_sweep(mach, sweep_deg, Rin_ratio, Re_per_in)
        elif b_in >= b1_guess and sweep_deg > _HIGH_SWEEP_DEG:
            Rt = _transition_reynolds_region3_high_sweep(mach, sweep_deg, Re_per_in)
        else:
            raise ValueError("no empirical equation for this combination of bluntness and sweep")

        # update b1 and b2 from the current Rt estimate
        b1 = _b1_bluntness_criterion(Tw_R, T_R, mach, Rt, Re_per_in, ycdelt)
        b2 = _b2_bluntness_criterion(Tw_R, Tn_R, Mn, Rt, Re_per_in, Rin_ratio)

        # check convergence of the bluntness-region boundaries
        if abs(b1 - b1_guess) < _BLUNTNESS_TOL_IN and abs(b2 - b2_guess) < _BLUNTNESS_TOL_IN:
            b1_guess, b2_guess = b1, b2
            break

        # update guesses for the next iteration
        b1_guess, b2_guess = b1, b2
    else:
        raise RuntimeError(f"bluntness-region iteration did not converge after {_BLUNTNESS_MAX_ITER} iterations")

    # convert the converged transition Reynolds number back to a physical
    # streamwise location using the freestream unit Reynolds number [1/m]
    return Rt / re1
