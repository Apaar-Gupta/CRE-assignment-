"""
Autocatalytic reaction:  A -> P,  rate = k * C_A * C_P   (product catalyzes its own formation)

Mass balance (constant volume, no side reactions): C_A + C_P = C_A0 + C_P0 = C_T0 (constant)

Integrating -dC_A/dt = k*C_A*(C_T0 - C_A) with partial fractions gives:

   ln(C_A / C_P) = ln(C_A0 / C_P0) - k * C_T0 * t

-> linear in (t, ln(C_A/C_P)), slope = -k*C_T0

Requires: C_A0 (usually just C_A data's first point) and C_P0 (initial product
concentration — must be > 0, since a purely zero product start has no
catalyst to kick the reaction off).
"""

import numpy as np

from utils.regression import linear_fit
from utils.validators import require_min_points, require_positive, require_present


def fit_autocatalytic(t, C_A, C_P0):
    require_min_points(t, "t", 3)
    require_present(C_P0, "C_P0 (initial product concentration)")
    require_positive(C_A, "C_A")

    C_P0 = float(C_P0)
    if C_P0 <= 0:
        raise ValueError(
            "C_P0 (initial product concentration) must be > 0 for an "
            "autocatalytic reaction — otherwise there's no catalyst to start it."
        )

    C_A = np.asarray(C_A, dtype=float)
    C_A0 = C_A[0]
    C_T0 = C_A0 + C_P0
    C_P = C_T0 - C_A

    if np.any(C_P <= 0):
        raise ValueError(
            "Computed C_P values went to zero or negative — check C_P0 and the C_A data."
        )

    y = np.log(C_A / C_P)
    fit = linear_fit(t, y)
    k = -fit["slope"] / C_T0

    return {
        "reaction_type": "Autocatalytic (A -> P, rate = k*C_A*C_P)",
        "equation": "ln(C_A/C_P) = ln(C_A0/C_P0) - k*(C_A0+C_P0)*t",
        "k": round(float(k), 6),
        "k_units": "1/(concentration*time)",
        "r_squared": fit["r_squared"],
        "plot": {
            "x_label": "t",
            "y_label": "ln(C_A/C_P)",
            "x_data": [float(v) for v in t],
            "y_data": y.tolist(),
            "fit_line": fit["fit_line"],
        },
    }
