"""Save simple false-positive and missed-detection evidence for the pilot test split."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
from rfdetr import RFDETRNano

ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = ROOT / "outputs" / "rfdetr_pilot_main_20260908" / "checkpoint_best_total.pth"
TEST_DIR = ROOT / "datasets" / "pilot_dataset_v1" / "rfdetr" / "test"
OUTPUT_DIR = ROOT / "outputs" / "rfdetr_pilot_main_20260908" / "error_examples"
THRESHOLD = 0.30
IOU_THRESHOLD = 0.50


def iou(left: list[float], right: list[float]) -> float:
    x1 = max(left[0], right[0])
    y1 = max(left[1], right[1])
    x2 = min(left[2], right[2])
    y2 = min(left[3], right[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    left_area = max(0.0, left[2] - left[0]) * max(0.0, left[3] - left[1])
    right_area = max(0.0, right[2] - right[0]) * max(0.0, right[3] - right[1])
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0


def main() -> None:
    annotation_path = TEST_DIR / "_annotations.coco.json"
    data = json.loads(annotation_path.read_text(encoding="utf-8"))
    image = data["images"][0]
    image_path = TEST_DIR / image["file_name"]
    category_names = {category["id"]: category["name"] for category in data["categories"]}

    ground_truth = []
    for annotation in data["annotations"]:
        x, y, width, height = annotation["bbox"]
        ground_truth.append(
            {
                "category_id": annotation["category_id"],
                "box": [x, y, x + width, y + height],
            }
        )

    model = RFDETRNano.from_checkpoint(str(CHECKPOINT))
    detections = model.predict(str(image_path), threshold=THRESHOLD)
    predictions = [
        {
            "category_id": int(category_id),
            "confidence": float(confidence),
            "box": [float(value) for value in box],
        }
        for box, category_id, confidence in zip(
            detections.xyxy.tolist(),
            detections.class_id.tolist(),
            detections.confidence.tolist(),
            strict=True,
        )
    ]

    matched_predictions: set[int] = set()
    matched_ground_truth: set[int] = set()
    for ground_truth_index, target in enumerate(ground_truth):
        candidates = [
            (prediction_index, iou(target["box"], prediction["box"]))
            for prediction_index, prediction in enumerate(predictions)
            if prediction_index not in matched_predictions
            and prediction["category_id"] == target["category_id"]
        ]
        if candidates:
            prediction_index, best_iou = max(candidates, key=lambda item: item[1])
            if best_iou >= IOU_THRESHOLD:
                matched_ground_truth.add(ground_truth_index)
                matched_predictions.add(prediction_index)

    misses = [
        target for index, target in enumerate(ground_truth) if index not in matched_ground_truth
    ]
    false_positives = [
        prediction
        for index, prediction in enumerate(predictions)
        if index not in matched_predictions
    ]

    image_bgr = cv2.imread(str(image_path))
    if image_bgr is None:
        raise RuntimeError(f"Could not read {image_path}")
    for target in ground_truth:
        x1, y1, x2, y2 = [round(value) for value in target["box"]]
        label = f"GT {category_names[target['category_id']]}"
        cv2.rectangle(image_bgr, (x1, y1), (x2, y2), (0, 200, 0), 2)
        cv2.putText(
            image_bgr,
            label,
            (x1, max(18, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 150, 0),
            2,
        )
    for prediction in predictions:
        x1, y1, x2, y2 = [round(value) for value in prediction["box"]]
        name = category_names.get(prediction["category_id"], prediction["category_id"])
        label = f"PRED {name} {prediction['confidence']:.2f}"
        cv2.rectangle(image_bgr, (x1, y1), (x2, y2), (0, 0, 220), 2)
        cv2.putText(
            image_bgr,
            label,
            (x1, min(image_bgr.shape[0] - 8, y2 + 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 220),
            2,
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    overlay_path = OUTPUT_DIR / "test_error_overlay.jpg"
    if not cv2.imwrite(str(overlay_path), image_bgr):
        raise RuntimeError(f"Could not save {overlay_path}")
    missed_dir = OUTPUT_DIR / "missed_detection_examples"
    false_positive_dir = OUTPUT_DIR / "false_positive_examples"
    missed_dir.mkdir(exist_ok=True)
    false_positive_dir.mkdir(exist_ok=True)
    missed_path = missed_dir / f"{image_path.stem}_missed.jpg"
    false_positive_path = false_positive_dir / f"{image_path.stem}_false_positive_check.jpg"
    if not cv2.imwrite(str(missed_path), image_bgr):
        raise RuntimeError(f"Could not save {missed_path}")
    if not cv2.imwrite(str(false_positive_path), image_bgr):
        raise RuntimeError(f"Could not save {false_positive_path}")

    summary = {
        "checkpoint": str(CHECKPOINT),
        "image": image["file_name"],
        "confidence_threshold": THRESHOLD,
        "iou_threshold": IOU_THRESHOLD,
        "ground_truth_count": len(ground_truth),
        "prediction_count": len(predictions),
        "missed_detection_count": len(misses),
        "false_positive_count": len(false_positives),
        "missed_detection_image": str(missed_path),
        "false_positive_check_image": str(false_positive_path),
        "missed_labels": [category_names[target["category_id"]] for target in misses],
        "false_positive_labels": [
            category_names.get(prediction["category_id"], str(prediction["category_id"]))
            for prediction in false_positives
        ],
    }
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
