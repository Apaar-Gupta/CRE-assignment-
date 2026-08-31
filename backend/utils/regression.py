"""
Shared linear-regression helper.

The integral method for reaction order determination works by transforming
concentration data so that the correct rate law becomes a STRAIGHT LINE
against time. Whichever candidate transform gives the best straight line
(highest R^2) is taken to be the correct order/model.

This module just does the actual line-fitting + R^2 calculation so every
model file (zero_order.py, first_order.py, ...) can reuse it.
"""

import numpy as np


def linear_fit(x, y):
    """
    Fit y = slope * x + intercept using least squares, and report R^2.

    Returns a dict with slope, intercept, r_squared, and the fitted y values
    (fit_line) so the frontend can plot data points + the fitted line together.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if x.shape[0] < 2:
        raise ValueError("Need at least 2 data points to fit a line.")

    slope, intercept = np.polyfit(x, y, 1)
    fit_line = slope * x + intercept

    ss_res = float(np.sum((y - fit_line) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))

    if ss_tot == 0:
        r_squared = 1.0 if ss_res == 0 else 0.0
    else:
        r_squared = 1.0 - (ss_res / ss_tot)

    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": round(float(r_squared), 6),
        "fit_line": fit_line.tolist(),
    }


def r_squared_from_arrays(y_actual, y_predicted):
    """R^2 for nonlinear fits (used by the series-reaction model)."""
    y_actual = np.asarray(y_actual, dtype=float)
    y_predicted = np.asarray(y_predicted, dtype=float)
    ss_res = float(np.sum((y_actual - y_predicted) ** 2))
    ss_tot = float(np.sum((y_actual - np.mean(y_actual)) ** 2))
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return round(1.0 - (ss_res / ss_tot), 6)
