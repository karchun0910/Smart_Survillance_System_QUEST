# Smart Surveillance Pilot Dataset v1

## Purpose

This pilot dataset supports the Smart Surveillance System's visible-object and laboratory-attire detection workflow. It is a small annotation and export test set, not a statistically representative training dataset.

## Current contents

- Selected images: 7 JPEG files.
- COCO annotations: 19 bounding boxes.
- Label categories: 12 project labels.
- Annotation export: `exports/pilot_dataset_v1_coco.zip` (merged batches 01 and 02).
- The CVAT export contains `annotations/instances_default.json`; local images remain in `selected_images` because the CVAT account could not export image files.

## Directory layout

```text
pilot_dataset_v1/
├── raw_images/
│   └── online_lab_attire/
│       ├── README.md
│       ├── sources.csv
│       └── source_metadata.json
├── selected_images/
├── annotations/
├── exports/
│   ├── pilot_dataset_v1_batch_01_coco.zip
│   ├── pilot_dataset_v1_batch_02_gowns_coco.zip
│   ├── pilot_dataset_v1_coco.zip
│   └── splits/
│       ├── train/
│       ├── validation/
│       └── test/
└── README.md
```

## Classes

The CVAT project uses these visible-object labels:

`person`, `lab_coat`, `lab_gown`, `long_pants`, `shoe`, `boot`, `sandal`, `slipper`, `food`, `drink_container`, `knife`, `handgun`.

Visible objects are annotated directly. Policy observations such as missing protective clothing or prohibited footwear are inferred later by the backend policy layer.

## Annotation rules

- Draw tight rectangles around visible objects.
- Annotate a partially visible object only when its class remains identifiable.
- Keep overlapping objects as separate annotations.
- Do not infer hidden footwear, trousers or clothing.
- Do not use a vague `dangerous_object` class.
- Use only approved images or harmless replicas for knife and handgun examples.

## Split layout

The current seven-image pipeline split is:

- `train`: `commons_25079653.jpg`, `commons_35489045.jpg`, `commons_86624682.jpg`, `commons_90407324.jpg`
- `validation`: `commons_103996749.jpg`, `commons_35489059.jpg`
- `test`: `commons_86850283.jpg`

This split is only for testing the dataset pipeline; it is too small for reliable model-performance claims.

## Source, licence and privacy

The current images were downloaded from Wikimedia Commons under the individual licences recorded in `raw_images/online_lab_attire/sources.csv`. CC BY sources require attribution; CC BY-SA sources also carry ShareAlike terms. Public-domain status is recorded as reported by each source page. The images do not inherit the Smart Surveillance System software licence.

The current batch uses public online source images because local laboratory attire was unavailable. It is not evidence of participant consent, local camera conditions or permission for face recognition. Do not upload identifiable images to a hosted service unless the project consent and university requirements allow it.

## Limitations and next work

This version contains seven selected images from a small online starter batch, including the second batch of laboratory-gown examples. It does not yet cover the planned lighting, distance, camera-angle, normal/violation or class-balance scenarios. Future versions should add consented local captures, more participants and backgrounds, quality review, balanced violations, and a larger documented train/validation/test split before model training.

Dataset version: `pilot_dataset_v1`
Status: pilot annotation and merged COCO export verified on 2026-09-06.
