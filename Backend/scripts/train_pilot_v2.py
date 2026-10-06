"""Prepare pilot v2 without session leakage, then fine-tune the existing Nano model."""

import json
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "datasets/pilot_dataset_v1/rfdetr"
V2 = ROOT / "datasets/pilot_dataset_v2"
DATASET = V2 / "rfdetr"
OUTPUT = ROOT / "outputs/rfdetr_pilot_v2_20261001"
WEIGHTS = ROOT / "outputs/rfdetr_pilot_main_20260908/checkpoint_best_total.pth"


def prepare():
    newer = json.loads((V2 / "exports/extracted/annotations/instances_default.json").read_text())
    counts = {}
    for split in ("train", "valid", "test"):
        original = json.loads((V1 / split / "_annotations.coco.json").read_text())
        assert original["categories"] == newer["categories"], "Class mapping differs"
        destination = DATASET / split
        destination.mkdir(parents=True, exist_ok=True)
        result = deepcopy(original)
        sources = {im["id"]: V1 / split / im["file_name"] for im in result["images"]}
        if split == "train":
            # Keep this single participant/session together, with v1 held-out sets unchanged.
            offset = max(im["id"] for im in result["images"])
            annotation_offset = max(a["id"] for a in result["annotations"])
            for image in newer["images"]:
                copied = deepcopy(image)
                copied["id"] += offset
                result["images"].append(copied)
                sources[copied["id"]] = V2 / "raw_images/jpeg" / image["file_name"]
            for annotation in newer["annotations"]:
                copied = deepcopy(annotation)
                copied["id"] += annotation_offset
                copied["image_id"] += offset
                result["annotations"].append(copied)
        category_ids = {c["id"] for c in result["categories"]}
        image_ids = {i["id"] for i in result["images"]}
        assert len(image_ids) == len(result["images"])
        for image in result["images"]:
            with Image.open(sources[image["id"]]) as opened:
                assert opened.size == (image["width"], image["height"]), sources[image["id"]]
                resized = opened.convert("RGB")
                resized.thumbnail((1600, 1600))
                sx, sy = resized.width / image["width"], resized.height / image["height"]
                for box in result["annotations"]:
                    if box["image_id"] != image["id"]:
                        continue
                    x, y, w, h = box["bbox"]
                    assert box["category_id"] in category_ids
                    assert 0 <= x < image["width"] and 0 <= y < image["height"]
                    assert (
                        w > 0
                        and h > 0
                        and x + w <= image["width"] + 1
                        and y + h <= image["height"] + 1
                    )
                    box["bbox"] = [x * sx, y * sy, w * sx, h * sy]
                    box["area"] = w * sx * h * sy
                image["width"], image["height"] = resized.size
                resized.save(destination / image["file_name"], quality=95)
        assert all(a["image_id"] in image_ids for a in result["annotations"])
        (destination / "_annotations.coco.json").write_text(json.dumps(result, indent=2))
        counts[split] = {
            "images": len(result["images"]),
            "annotations": dict(Counter(a["category_id"] for a in result["annotations"])),
        }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": str(V2),
        "splits": counts,
        "limitations": (
            "11 v2 images from one coat-and-pants participant/session; no v2 absence examples. "
            "v1 validation/test unchanged, no v2 session leakage."
        ),
        "initial_weights": str(WEIGHTS),
    }
    (OUTPUT / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(counts, flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    prepare()
    import torch
    from rfdetr import RFDETRNano

    assert torch.cuda.is_available(), "CUDA required for this bounded demo run"
    model = RFDETRNano(pretrain_weights=str(WEIGHTS), device="cuda", num_classes=12)
    model.train(
        dataset_dir=str(DATASET),
        output_dir=str(OUTPUT),
        epochs=10,
        batch_size=1,
        grad_accum_steps=1,
        num_workers=0,
        seed=42,
        tensorboard=False,
        wandb=False,
        run_test=True,
    )
