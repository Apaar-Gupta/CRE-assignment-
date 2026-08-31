"""
Series reaction:  A -k1-> B -k2-> C, both steps first order.

Step 1 is simple first order in A:
    C_A(t) = C_A0 * exp(-k1 * t)
    -> k1 found the same way as the first-order model (ln(C_A) vs t).

Step 2's solution for the intermediate B (assuming C_B0 = 0) is:
    C_B(t) = (C_A0 * k1 / (k2 - k1)) * (exp(-k1*t) - exp(-k2*t))

This is NOT linear in any simple transform, so k2 is found with a
nonlinear least-squares fit (scipy.optimize.curve_fit), holding k1 fixed
at the value already found from the C_A data.

Requires: t, C_A data, and C_B data (concentration of the intermediate
at the same time points). Assumes C_B0 = 0 (no B present initially,
the standard textbook setup for this problem).
"""

import numpy as np
from scipy.optimize import curve_fit

from utils.regression import linear_fit, r_squared_from_arrays
from utils.validators import require_min_points, require_positive, require_present


def _cb_model(t, k1, k2, C_A0):
    # Guard against k1 == k2 (degenerate case) by nudging k2 slightly
    if abs(k2 - k1) < 1e-9:
        k2 = k1 + 1e-6
    return (C_A0 * k1 / (k2 - k1)) * (np.exp(-k1 * t) - np.exp(-k2 * t))


def fit_series_reaction(t, C_A, C_B):
    require_min_points(t, "t", 3)
    require_present(C_B, "C_B data (intermediate concentration)")
    require_positive(C_A, "C_A")

    t = np.asarray(t, dtype=float)
    C_A = np.asarray(C_A, dtype=float)
    C_B = np.asarray(C_B, dtype=float)
    C_A0 = C_A[0]

    # --- Step 1: k1 from C_A, exactly like first order ---
    y1 = np.log(C_A)
    fit1 = linear_fit(t, y1)
    k1 = -fit1["slope"]

    # --- Step 2: k2 from C_B via nonlinear fit, k1 held fixed ---
    def model(t_, k2):
        return _cb_model(t_, k1, k2, C_A0)

    # initial guess: something a bit different from k1
    k2_guess = max(k1 * 2, 1e-3)
    try:
        popt, _ = curve_fit(model, t, C_B, p0=[k2_guess], maxfev=10000)
        k2 = float(popt[0])
    except RuntimeError as exc:
        raise ValueError(
            f"Could not fit k2 for the series reaction (curve_fit did not converge): {exc}"
        )

    C_B_fit = _cb_model(t, k1, k2, C_A0)
    r2_b = r_squared_from_arrays(C_B, C_B_fit)

    return {
        "reaction_type": "Series Reaction (A -> B -> C)",
        "equation": "C_A=C_A0*exp(-k1 t);  C_B=(C_A0 k1/(k2-k1))*(exp(-k1 t)-exp(-k2 t))",
        "k1": round(float(k1), 6),
        "k2": round(float(k2), 6),
        "k_units": "1/time",
        "r_squared": round(float((fit1["r_squared"] + r2_b) / 2), 6),
        "r_squared_step1_A": fit1["r_squared"],
        "r_squared_step2_B": r2_b,
        "plot": {
            "x_label": "t",
            "y_label": "Concentration",
            "x_data": t.tolist(),
            "series": [
                {"name": "C_A (data)", "y_data": C_A.tolist(), "type": "scatter"},
                {"name": "C_A (fit)", "y_data": np.exp(-k1 * t + fit1["intercept"]).tolist(), "type": "line"},
                {"name": "C_B (data)", "y_data": C_B.tolist(), "type": "scatter"},
                {"name": "C_B (fit)", "y_data": C_B_fit.tolist(), "type": "line"},
            ],
        },
    }
