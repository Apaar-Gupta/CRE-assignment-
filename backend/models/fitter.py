"""
Top-level dispatcher.

MANUAL mode: the user picked a specific reaction type -> run just that model.
AUTO mode:   try every model for which the user supplied enough data, and
             return them all ranked by R^2 (closest to 1 = best fit),
             which is exactly what "trial and error" order-finding does,
             just automated.
"""

from models.zero_order import fit_zero_order
from models.first_order import fit_first_order
from models.second_order import fit_second_order_uni, fit_second_order_bimolecular
from models.autocatalytic import fit_autocatalytic
from models.series_reaction import fit_series_reaction
from models.reversible_reaction import fit_reversible


MANUAL_DISPATCH = {
    "zero_order": lambda p: fit_zero_order(p["t"], p["C_A"]),
    "first_order": lambda p: fit_first_order(p["t"], p["C_A"]),
    "second_order_uni": lambda p: fit_second_order_uni(p["t"], p["C_A"]),
    "second_order_bimolecular": lambda p: fit_second_order_bimolecular(
        p["t"], p["C_A"], p["C_A"][0], p.get("C_B0")
    ),
    "autocatalytic": lambda p: fit_autocatalytic(p["t"], p["C_A"], p.get("C_P0")),
    "series": lambda p: fit_series_reaction(p["t"], p["C_A"], p.get("C_B_data")),
    "reversible": lambda p: fit_reversible(
        p["t"], p["C_A"], p.get("C_Ae"), p.get("C_B0", 0.0)
    ),
}

REACTION_TYPE_LABELS = {
    "zero_order": "Zero Order",
    "first_order": "First Order",
    "second_order_uni": "Second Order (Unimolecular)",
    "second_order_bimolecular": "Second Order (Bimolecular)",
    "autocatalytic": "Autocatalytic",
    "series": "Series (A -> B -> C)",
    "reversible": "Reversible (A <=> B)",
}


def run_manual(reaction_type, payload):
    if reaction_type not in MANUAL_DISPATCH:
        raise ValueError(f"Unknown reaction_type '{reaction_type}'")
    return MANUAL_DISPATCH[reaction_type](payload)


def run_auto(payload):
    """
    Try every model for which we have sufficient data, then rank them.

    IMPORTANT RANKING RULE:
    "zero_order", "first_order", and "second_order_uni" only ever look at
    the C_A column. If the user also supplied C_B data (series), C_Ae
    (reversible), C_B0 (bimolecular), or C_P0 (autocatalytic), those richer
    models are fit against MORE of the data the user actually measured.

    A classic trap: for a series reaction A->B->C, step 1 is itself plain
    first-order decay of A, so "First Order" (which only ever looks at C_A)
    will often get a near-perfect R^2 too - same as k1 in the series fit.
    But it completely ignores the intermediate (C_B) profile, which is the
    whole reason to suspect a series mechanism in the first place. Comparing
    its R^2 directly against the series model's R^2 (which is scored on
    BOTH curves) is an apples-to-oranges comparison, and would wrongly
    declare "First Order" the winner just because it was graded on an
    easier subset of the data.

    Fix: any model that consumes extra data the user actually provided
    (call these "data-complete" models) is preferred for best_fit over the
    single-species-only models, as long as its fit is reasonably good
    (R^2 >= 0.9). Only if no data-complete model reaches that bar do we
    fall back to plain R^2 ranking across everything.
    """
    results = []
    errors = []

    # Track which result dicts came from "data-complete" models, i.e. ones
    # that used extra data the user filled in beyond plain t + C_A.
    data_complete_flags = {}  # id(result) -> True

    always_try = ["zero_order", "first_order", "second_order_uni"]
    for name in always_try:
        try:
            r = MANUAL_DISPATCH[name](payload)
            r["uses_full_dataset"] = False
            results.append(r)
        except Exception as exc:  # noqa: BLE001
            errors.append({"reaction_type": REACTION_TYPE_LABELS[name], "error": str(exc)})

    conditional_try = []
    if payload.get("C_B0") not in (None, ""):
        conditional_try.append("second_order_bimolecular")
    if payload.get("C_P0") not in (None, ""):
        conditional_try.append("autocatalytic")
    if payload.get("C_B_data"):
        conditional_try.append("series")
    if payload.get("C_Ae") not in (None, ""):
        conditional_try.append("reversible")

    for name in conditional_try:
        try:
            r = MANUAL_DISPATCH[name](payload)
            r["uses_full_dataset"] = True
            results.append(r)
        except Exception as exc:  # noqa: BLE001
            errors.append({"reaction_type": REACTION_TYPE_LABELS[name], "error": str(exc)})

    results.sort(key=lambda r: r["r_squared"], reverse=True)

    # --- Pick best_fit, preferring data-complete models above a quality bar ---
    QUALITY_BAR = 0.90
    data_complete_candidates = [r for r in results if r.get("uses_full_dataset") and r["r_squared"] >= QUALITY_BAR]

    if data_complete_candidates:
        best_fit = data_complete_candidates[0]  # already sorted by r_squared desc
        best_fit["priority_note"] = (
            "Selected over models with a higher raw R\u00b2 because this model "
            "explains ALL the data you provided (including the extra "
            "concentration profile), while the others only fit C_A and "
            "silently ignore the rest."
        )
    else:
        best_fit = results[0] if results else None

    return {
        "best_fit": best_fit,
        "all_results": results,
        "errors": errors,
    }
