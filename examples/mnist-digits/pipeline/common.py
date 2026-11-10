"""Paths, contract constants and metrics shared by the pipeline scripts (canvas E, A, N)."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, recall_score

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "digits.csv"
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
EXPERIMENTS = ROOT / "experiments"
REPORTS = ROOT / "reports"

SEED = 42
ROUND = 2
PREPROCESSING = ["drop"]
ID = "image_id"
TARGET = "digit"
PIXELS = [f"pixel_{row}_{col}" for row in range(8) for col in range(8)]
SPLITS = ("train", "validation", "test")

PRIMARY = "accuracy"
PRIMARY_TARGET = 0.97
GUARDRAIL = "min_class_recall"
GUARDRAIL_TARGET = 0.90


def load_split(name: str) -> tuple[pd.DataFrame, pd.Series]:
    frame = pd.read_csv(PROCESSED / f"{name}.csv")
    return frame[PIXELS], frame[TARGET]


def score(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    per_class = recall_score(y_true, y_pred, average=None)
    return {
        PRIMARY: round(float(accuracy_score(y_true, y_pred)), 4),
        GUARDRAIL: round(float(np.min(per_class)), 4),
    }
