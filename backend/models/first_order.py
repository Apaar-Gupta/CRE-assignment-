"""
First order:  A -> Products,   -dC/dt = k*C
Integrated:   ln(C) = ln(C0) - k t   -> linear in (t, ln C), slope = -k
"""

import numpy as np

from utils.regression import linear_fit
from utils.validators import require_min_points, require_positive


def fit_first_order(t, C):
    require_min_points(t, "t", 3)
    require_positive(C, "C")

    y = np.log(C)
    fit = linear_fit(t, y)
    k = -fit["slope"]

    return {
        "reaction_type": "First Order",
        "equation": "ln(C) = ln(C0) - k*t",
        "k": round(k, 6),
        "k_units": "1/time",
        "r_squared": fit["r_squared"],
        "plot": {
            "x_label": "t",
            "y_label": "ln(C)",
            "x_data": [float(v) for v in t],
            "y_data": y.tolist(),
            "fit_line": fit["fit_line"],
        },
    }
