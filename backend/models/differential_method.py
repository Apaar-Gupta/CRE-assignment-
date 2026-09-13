"""
Differential method for determining reaction order and rate constant.

Unlike the integral method (which guesses an integer order, integrates the
rate law, and checks which guess linearizes the data), the differential
method works directly with the RATE of reaction and never needs to guess
an order at all — it comes out as a direct regression result, and can be
any real number (including decimals), not just 0, 1, or 2.

THE CORE IDEA:

For an nth order reaction:  -dC_A/dt = k * C_A^n

Taking the natural log of both sides:

    ln(-dC_A/dt) = ln(k) + n * ln(C_A)

This is linear in (ln(C_A), ln(rate)) with:
    slope     = n   (the reaction order — a direct fit, can be decimal)
    intercept = ln(k)   ->   k = exp(intercept)

THE PRACTICAL CHALLENGE:

We only ever have C_A measured at discrete time points, not a continuous
function, so -dC_A/dt has to be ESTIMATED numerically at each data point
before any of the above can be used. This is the step the integral method
never needs (it works with the integrated concentration profile directly).

We estimate the local slope dC_A/dt at every point using NumPy's gradient
function, which:
  - uses a central (both-sided) difference at interior points, and
  - uses a one-sided (forward/backward) difference at the two endpoints,
  - and correctly handles unevenly spaced time data.

Once we have a rate estimate at each point, any point where the estimated
rate or C_A itself is not strictly positive is dropped (ln is undefined
there) before running the linear regression described above.
"""

import numpy as np

from utils.regression import linear_fit
from utils.validators import require_min_points, require_positive, require_arrays_same_length


def fit_differential_method(t, C_A):
    require_min_points(t, "t", 4)
    require_positive(C_A, "C_A")
    require_arrays_same_length(("t", t), ("C_A", C_A))

    t = np.asarray(t, dtype=float)
    C_A = np.asarray(C_A, dtype=float)

    # --- Step 1: numerically estimate -dC_A/dt at every data point ---
    dCdt = np.gradient(C_A, t)
    rate = -dCdt  # rate of consumption of A (should be positive if A is decreasing)

    # --- Step 2: build the full per-point calculation table (for transparency) ---
    # Keep every point here, valid or not, so the frontend can show exactly
    # which points were used and which were excluded, and why.
    table = []
    for i in range(len(t)):
        row = {
            "t": float(t[i]),
            "C_A": float(C_A[i]),
            "rate": float(rate[i]),
            "used": bool(rate[i] > 0),
        }
        table.append(row)

    # --- Step 3: filter to only the points usable in a log-log regression ---
    mask = rate > 0
    n_excluded = int(np.sum(~mask))

    if np.sum(mask) < 3:
        raise ValueError(
            "Not enough valid points to fit the differential method: at least 3 "
            "points with a positive estimated rate (-dC_A/dt > 0) are needed, but "
            f"only {int(np.sum(mask))} were found. This usually means C_A isn't "
            "consistently decreasing over time."
        )

    ln_C = np.log(C_A[mask])
    ln_rate = np.log(rate[mask])

    # --- Step 4: linear regression of ln(rate) vs ln(C_A) ---
    # slope = order (n), intercept = ln(k)
    fit = linear_fit(ln_C, ln_rate)
    order = fit["slope"]
    k = float(np.exp(fit["intercept"]))

    # Fill in ln(C_A), ln(rate), and the fit's predicted ln(rate) for every
    # USED row of the table, so the frontend can show the full log-log
    # calculation alongside the raw t/C_A/rate table.
    fit_idx = 0
    for row in table:
        if row["used"]:
            row["ln_C_A"] = float(ln_C[fit_idx])
            row["ln_rate"] = float(ln_rate[fit_idx])
            row["ln_rate_fit"] = float(fit["fit_line"][fit_idx])
            fit_idx += 1
        else:
            row["ln_C_A"] = None
            row["ln_rate"] = None
            row["ln_rate_fit"] = None

    return {
        "reaction_type": f"Differential Method (order n = {round(order, 4)})",
        "equation": "ln(-dC_A/dt) = ln(k) + n*ln(C_A)",
        "order": round(float(order), 4),
        "k": round(k, 6),
        "k_units": "(concentration)^(1-n) / time",
        "r_squared": fit["r_squared"],
        "slope": round(fit["slope"], 6),
        "intercept": round(fit["intercept"], 6),
        "n_points_used": int(np.sum(mask)),
        "n_points_excluded": n_excluded,
        "table": table,
        "plot": {
            "x_label": "ln(C_A)",
            "y_label": "ln(-dC_A/dt)",
            "x_data": ln_C.tolist(),
            "y_data": ln_rate.tolist(),
            "fit_line": fit["fit_line"],
        },
    }
