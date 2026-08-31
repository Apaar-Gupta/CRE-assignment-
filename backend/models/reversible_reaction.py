"""
Reversible reaction:  A <=>(k1, k2)=> B, both directions first order.
    -dC_A/dt = k1*C_A - k2*C_B

Using the mass balance C_A + C_B = C_A0 + C_B0 (constant), and C_Ae = the
equilibrium concentration of A (where the reaction appears to stop), the
integrated rate law is:

    ln[(C_A0 - C_Ae) / (C_A - C_Ae)] = (k1 + k2) * t

-> linear in (t, that log term), slope = (k1 + k2)

At equilibrium the forward and reverse rates are equal:
    k1 * C_Ae = k2 * C_Be   =>   k1/k2 = C_Be/C_Ae = K_eq

Combined with (k1 + k2) from the slope, we can solve for k1 and k2 individually.

Requires: t, C_A data, C_Ae (equilibrium concentration of A), and
optionally C_B0 (defaults to 0 if not given).
"""

import numpy as np

from utils.regression import linear_fit
from utils.validators import require_min_points, require_present


def fit_reversible(t, C_A, C_Ae, C_B0=0.0):
    require_min_points(t, "t", 3)
    require_present(C_Ae, "C_Ae (equilibrium concentration of A)")

    t = np.asarray(t, dtype=float)
    C_A = np.asarray(C_A, dtype=float)
    C_Ae = float(C_Ae)
    C_B0 = float(C_B0 or 0.0)
    C_A0 = C_A[0]

    if C_Ae >= C_A0:
        raise ValueError("C_Ae (equilibrium concentration) must be less than C_A0.")

    denom = C_A - C_Ae
    if np.any(denom <= 0):
        raise ValueError(
            "Some C_A values are at or below C_Ae — the reaction should "
            "approach but not cross the equilibrium concentration. Check your data."
        )

    y = np.log((C_A0 - C_Ae) / denom)
    fit = linear_fit(t, y)
    k1_plus_k2 = fit["slope"]

    if k1_plus_k2 <= 0:
        raise ValueError("Fitted (k1+k2) came out <= 0 — check the C_A / C_Ae data.")

    C_Be = C_A0 + C_B0 - C_Ae
    if C_Be <= 0:
        raise ValueError("Computed C_Be (equilibrium concentration of B) is <= 0.")

    K_eq = C_Be / C_Ae  # = k1 / k2
    k2 = k1_plus_k2 / (1.0 + K_eq)
    k1 = k1_plus_k2 - k2

    return {
        "reaction_type": "Reversible Reaction (A <=> B)",
        "equation": "ln[(C_A0-C_Ae)/(C_A-C_Ae)] = (k1+k2)*t,  K_eq=k1/k2=C_Be/C_Ae",
        "k1": round(float(k1), 6),
        "k2": round(float(k2), 6),
        "K_eq": round(float(K_eq), 6),
        "k_units": "1/time",
        "r_squared": fit["r_squared"],
        "plot": {
            "x_label": "t",
            "y_label": "ln[(C_A0-C_Ae)/(C_A-C_Ae)]",
            "x_data": t.tolist(),
            "y_data": y.tolist(),
            "fit_line": fit["fit_line"],
        },
    }
