"""
Zero order:  A -> Products,   -dC/dt = k
Integrated:  C = C0 - k t     -> linear in (t, C), slope = -k
"""

from utils.regression import linear_fit
from utils.validators import require_min_points


def fit_zero_order(t, C):
    require_min_points(t, "t", 3)
    fit = linear_fit(t, C)
    k = -fit["slope"]

    return {
        "reaction_type": "Zero Order",
        "equation": "C = C0 - k*t",
        "k": round(k, 6),
        "k_units": "concentration/time",
        "r_squared": fit["r_squared"],
        "plot": {
            "x_label": "t",
            "y_label": "C",
            "x_data": [float(v) for v in t],
            "y_data": [float(v) for v in C],
            "fit_line": fit["fit_line"],
        },
    }
