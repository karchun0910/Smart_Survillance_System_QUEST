from pathlib import Path

import cv2
import supervision as sv
import torch
from rfdetr import RFDETRNano
from rfdetr.assets.coco_classes import COCO_CLASSES

IMAGE_PATH = Path(__file__).resolve().parents[2] / "outputs" / "webcam_capture.jpg"
OUTPUT_PATH = Path(__file__).resolve().parents[2] / "outputs" / "rfdetr_webcam_person.jpg"
CONFIDENCE_THRESHOLD = 0.5
PERSON_CLASS_ID = 1


def main() -> None:
    model = RFDETRNano()
    model.inference(compile=False, dtype=torch.float16, inplace=True)

    detections = model.predict(str(IMAGE_PATH), threshold=CONFIDENCE_THRESHOLD)
    detections = detections[detections.class_id == PERSON_CLASS_ID]
    labels = [
        f"{COCO_CLASSES[int(class_id)]} {confidence:.2f}"
        for class_id, confidence in zip(
            detections.class_id,
            detections.confidence,
            strict=True,
        )
    ]

    image = detections.metadata["source_image"].copy()
    image = sv.BoxAnnotator().annotate(image, detections)
    image = sv.LabelAnnotator().annotate(image, detections, labels)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    saved = cv2.imwrite(
        str(OUTPUT_PATH),
        cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
    )
    if not saved:
        raise RuntimeError(f"Could not save detection result to {OUTPUT_PATH}")

    print(f"Detected: {', '.join(labels) or 'nothing above threshold'}")
    print(f"Saved result: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
