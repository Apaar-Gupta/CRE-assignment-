"""
Second order, unimolecular:  2A -> Products,  -dC_A/dt = k*C_A^2
Integrated:  1/C = 1/C0 + k t   -> linear in (t, 1/C), slope = +k

Second order, bimolecular:  A + B -> Products,  -dC_A/dt = k*C_A*C_B
(requires C_A0 != C_B0)
Integrated:  ln(C_B/C_A) = ln(C_B0/C_A0) + k(C_B0 - C_A0) t
             -> linear in (t, ln(C_B/C_A)), slope = k*(C_B0 - C_A0)

For the bimolecular case we assume 1:1 stoichiometry, so at any time:
   C_B(t) = C_B0 - (C_A0 - C_A(t))
i.e. however much A has reacted, the same amount of B has reacted.
"""

import numpy as np

from utils.regression import linear_fit
from utils.validators import require_min_points, require_positive, require_present


def fit_second_order_uni(t, C):
    require_min_points(t, "t", 3)
    require_positive(C, "C")

    y = 1.0 / np.asarray(C, dtype=float)
    fit = linear_fit(t, y)
    k = fit["slope"]

    return {
        "reaction_type": "Second Order (Unimolecular, 2A -> P)",
        "equation": "1/C = 1/C0 + k*t",
        "k": round(k, 6),
        "k_units": "1/(concentration*time)",
        "r_squared": fit["r_squared"],
        "plot": {
            "x_label": "t",
            "y_label": "1/C",
            "x_data": [float(v) for v in t],
            "y_data": y.tolist(),
            "fit_line": fit["fit_line"],
        },
    }


def fit_second_order_bimolecular(t, C_A, C_A0, C_B0):
    require_min_points(t, "t", 3)
    require_present(C_B0, "C_B0 (initial concentration of B)")
    require_positive(C_A, "C_A")

    C_A0 = float(C_A0)
    C_B0 = float(C_B0)

    if abs(C_B0 - C_A0) < 1e-12:
        raise ValueError(
            "Bimolecular second order requires C_A0 != C_B0. "
            "If C_A0 == C_B0, use 'Second Order (Unimolecular)' instead."
        )

    C_A = np.asarray(C_A, dtype=float)
    reacted = C_A0 - C_A
    C_B = C_B0 - reacted

    if np.any(C_B <= 0):
        raise ValueError(
            "Computed C_B values went to zero or negative — check that "
            "C_A0, C_B0 and the C_A data are consistent (1:1 stoichiometry assumed)."
        )

    y = np.log(C_B / C_A)
    fit = linear_fit(t, y)
    k = fit["slope"] / (C_B0 - C_A0)

    return {
        "reaction_type": "Second Order (Bimolecular, A + B -> P)",
        "equation": "ln(C_B/C_A) = ln(C_B0/C_A0) + k*(C_B0 - C_A0)*t",
        "k": round(float(k), 6),
        "k_units": "1/(concentration*time)",
        "r_squared": fit["r_squared"],
        "plot": {
            "x_label": "t",
            "y_label": "ln(C_B/C_A)",
            "x_data": [float(v) for v in t],
            "y_data": y.tolist(),
            "fit_line": fit["fit_line"],
        },
    }
