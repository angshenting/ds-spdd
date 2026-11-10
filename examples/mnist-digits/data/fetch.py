"""Write scikit-learn's bundled handwritten digits to data/raw/digits.csv.

The images are the UCI "Optical Recognition of Handwritten Digits" test set:
8x8 grids of 0-16 ink counts, one row per image. No network access needed.
"""

from pathlib import Path

from sklearn.datasets import load_digits

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "digits.csv"


def main() -> None:
    frame = load_digits(as_frame=True).frame.rename(columns={"target": "digit"})
    frame.insert(0, "image_id", range(len(frame)))
    frame = frame.astype("int64")
    RAW.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RAW, index=False)
    print(f"wrote {len(frame)} rows x {frame.shape[1]} columns to {RAW.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
