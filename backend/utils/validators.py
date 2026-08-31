"""
Basic sanity checks on incoming data so the models fail with a clear
message instead of a cryptic numpy/scipy traceback.
"""


class ValidationError(Exception):
    pass


def require_arrays_same_length(*arrays_with_names):
    """arrays_with_names: list of (name, array) tuples."""
    lengths = {name: len(arr) for name, arr in arrays_with_names}
    unique_lengths = set(lengths.values())
    if len(unique_lengths) > 1:
        raise ValidationError(
            f"Arrays must be the same length, got: {lengths}"
        )


def require_min_points(arr, name, minimum=3):
    if len(arr) < minimum:
        raise ValidationError(
            f"'{name}' needs at least {minimum} data points, got {len(arr)}."
        )


def require_positive(arr, name):
    if any(v <= 0 for v in arr):
        raise ValidationError(
            f"All values in '{name}' must be > 0 (this model uses a log or "
            f"reciprocal transform, which is undefined at 0 or negative values)."
        )


def require_present(value, name):
    if value is None or value == "":
        raise ValidationError(f"'{name}' is required for this reaction type.")
    return value
