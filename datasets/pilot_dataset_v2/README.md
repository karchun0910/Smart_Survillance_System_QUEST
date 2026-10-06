# Pilot Dataset v2

Status date: 2026-10-01

## Current batch

- 11 consented JPEG images with matching DNG masters.
- 11 images, 44 boxes and 12 category definitions in the corrected COCO export.
- Represented boxes: `person` 11, `lab_coat` 11, `long_pants` 11, `shoe` 4 and `slipper` 7.
- All image references, category IDs and bounding boxes pass structural validation.
- No exact duplicate image files were found.
- All images come from one participant, session and background, so they must stay in the same dataset split.

## Prepared demo training dataset

The corrected export includes the `long_pants` box for `IMG_1195.jpg` and the `lab_coat` box for `IMG_1199.jpg`.

`Backend/scripts/train_pilot_v2.py` validates image dimensions, category IDs and every box, then creates resized JPEG copies under `rfdetr/`. Originals remain unchanged. All 11 v2 images stay together in training alongside the four v1 training images. The original two v1 validation images and one test image remain held out. The 12 class IDs and names are unchanged.

This is a limited demo fine-tune, not a completed diverse dataset. All v2 images show one participant wearing both a coat and long pants; they provide no v2 missing-attire examples. Validation contains no long-pants boxes, and the test set contains only one. These sets cannot establish reliable generalisation or missing-attire accuracy.

## Additional capture target

Collect at least 19 more images to reach the minimum target of 30. Include:

- lab coat with long pants;
- missing lab coat with long pants;
- lab coat with missing long pants;
- missing lab coat with missing long pants.

Use at least two additional participants or sessions. Vary front, side and rear views, near and far distance, bright and dim lighting, and more than one background. Keep each participant/session group together when the train, validation and test splits are created.

## Next steps

1. Capture and annotate the remaining varied examples.
2. Review every image and box; remove unusable or redundant frames.
3. Create broader group-aware train, validation and test splits.
4. Retrain and evaluate against independent normal and missing-attire sessions.
