from typing import Final


CANONICAL_MEASUREMENT_FIELDS: Final[tuple[str, ...]] = (
    "chest_upper_in",
    "chest_lower_in",
    "waist_upper_in",
    "waist_lower_in",
    "sleeve_in",
    "shoulder_in",
    "inseam_in",
    "hip_in",
)

MEASUREMENT_MIN_IN: Final[float] = 4.0
MEASUREMENT_MAX_IN: Final[float] = 80.0

DEFAULT_LIST_LIMIT: Final[int] = 50
MAX_LIST_LIMIT: Final[int] = 200
