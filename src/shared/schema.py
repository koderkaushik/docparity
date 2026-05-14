from dataclasses import dataclass, field
from enum import Enum


class DriftType(Enum):
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    NO_DRIFT = "no-drift"


@dataclass
class DriftDetails:
    type: DriftType
    description: str
    severity: str | None = None
    missing_params: list[str] = field(default_factory=list)
    extra_params_in_doc: list[str] = field(default_factory=list)
    type_mismatches: list[dict] = field(default_factory=list)
    behavioral_mismatches: list[str] = field(default_factory=list)


@dataclass
class Entry:
    entry_id: str
    source: str
    origin_repo: str
    origin_file: str
    origin_function: str
    code: str
    docstring: str
    full_source: str
    drift_label: DriftType | None = None
    drift_present: bool | None = None
    drift_details: DriftDetails | None = None
    origin_commit: str | None = None
    ground_truth_annotation: dict | None = None


@dataclass
class Prediction:
    entry_id: str
    approach: str
    predicted_label: DriftType
    predicted_details: dict | None = None
    raw_output: str | None = None