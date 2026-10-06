# Smart Surveillance Project Handbook

Last updated: **2026-09-22**

## Completed

### 2026-09-06 — Pilot dataset merge

- Merged CVAT batches 01 and 02 into `datasets/pilot_dataset_v1/exports/pilot_dataset_v1_coco.zip`.
- Verified 7 images, 19 annotations, 12 category definitions and valid image references.
- Updated the pipeline split: train 4, validation 2, test 1.

### 2026-09-08 — RF-DETR preflight

- Validated the merged COCO export and split files.
- Confirmed all 12 class IDs are present.
- Confirmed the project environment: Python 3.12.10, PyTorch 2.11.0+cu128, CUDA available, NVIDIA GeForce RTX 3050 Laptop GPU, RF-DETR 1.9.4.
- Checked class balance: `person` 10, `lab_coat` 4, `lab_gown` 3, `long_pants` 2; the remaining 8 classes currently have 0 boxes.

### 2026-09-08 — RF-DETR Nano smoke test

- Built `datasets/pilot_dataset_v1/rfdetr` with RF-DETR `train`, `valid`, and `test` folders.
- Ran one GPU epoch at 384px with batch size 1.
- Smoke test completed successfully after setting UTF-8 console output.
- Validation result: mAP 50:95 `0.1012`, mAP 50 `0.1725`, precision `0.1667`, recall `0.3333`, F1 `0.2222`.
- Saved checkpoints and metrics under `outputs/rfdetr_pilot_smoke_utf8`.

### 2026-09-08 — RF-DETR Nano pilot training and evaluation

- Completed 10 epochs at 384px with batch size 1 on the RTX 3050 GPU.
- Saved checkpoints and training logs under `outputs/rfdetr_pilot_main_20260908`.
- Selected `checkpoint_best_total.pth`; it was chosen from the best validation score (regular mAP50:95 `0.4667`, epoch 3).
- Test result: mAP50:95 `0.1944`, mAP50 `0.3333`, precision `0.3333`, recall `0.3333`.
- Test per-class result: `lab_coat` AP50:95 `0.5833`; `person` and `long_pants` AP50:95 `0.0000`.
- Saved error evidence under `outputs/rfdetr_pilot_main_20260908/error_examples`: 3 missed detections and 0 false positives at confidence `0.30`.

### 2026-09-08 — Pilot snapshot frozen

- Frozen artifact: `datasets/pilot_dataset_v1/exports/pilot_dataset_v1_coco.zip`.
- SHA-256: `1B5E4B2A3E6A9740DDCBA1A5F5165078534C1E25E3345FDC9D14F8D9C1F5997D`.
- This is a reproducible pilot snapshot, not a final-quality 12-class training dataset.

## Current status — 2026-09-08

The two-day RF-DETR pipeline is complete for this pilot snapshot. The metrics are not a quality claim because the dataset is tiny and eight planned classes still have no annotations.

## Upcoming tasks

1. Add annotated examples for `shoe`, `boot`, `sandal`, `slipper`, `food`, `drink_container`, `knife`, and `handgun` (use harmless replicas for prohibited-object examples).
2. Create dataset version `pilot_dataset_v2` and repeat the training/evaluation pipeline.

## 2026-09-08 — Observation, event, and dashboard MVP

### Completed and locally verified

- Added validated observation storage with camera ID, track ID, class label, confidence, timestamp, bounding box, model version, visible duration, identity, and evidence path.
- Added configurable policy thresholds (`confidence_threshold`, `min_duration_seconds`) and cooldown-aware event creation.
- Added event list/detail/review APIs under `/api/v1/events` and observation ingestion under `/api/v1/observations`.
- Added an Alembic migration for the policy fields, `observations` table, and `events` table; offline SQL generation passed.
- Updated the live RF-DETR webcam script to use ByteTrack IDs, configurable confidence threshold, FPS, and latency display.
- Added per-track visible-time calculation to the overlay and observation payload.
- Added optional detector-to-dashboard posting (`RFDETR_POST_OBSERVATIONS=1`) with one observation per tracked person per second; it defaults off for a local-only preview.
- Updated the React dashboard to show recent events, camera/track IDs, severity, timestamps, confirmed/normal styling, and lecturer review actions.
- Added dashboard controls for rule confidence thresholds and minimum visible duration.
- Backend tests: **4 passed**; backend Ruff checks and Python compilation passed.
- Frontend lint, TypeScript/Vite production build, and Prettier checks passed.
- Fixed the webcam display environment by removing conflicting unused `opencv-python-headless`, `roboflow`, and `rf100vl` packages and restoring `opencv-python 4.14.0`; OpenCV now reports the Windows `WIN32UI` GUI backend.
- Applied migration `8b3e1c2a4d77` to the real MySQL database and confirmed it is at Alembic head.
- Manually verified the MySQL-backed flow: rule creation, event creation, dashboard display, lecturer confirmation, cooldown duplicate prevention, confidence filtering, and minimum-duration filtering.
- Manually verified the physical webcam loop: RF-DETR bounding box, confidence `0.97`, stable ByteTrack ID `#1`, visible time `39.7s`, approximately `15.8 FPS`, and `63.1 ms` displayed latency.
- Manually verified brief occlusion/re-entry and simultaneous multi-person tracking; bounding boxes followed the subjects and ByteTrack assigned tracking IDs successfully.
- Verified live detector observations were persisted in MySQL with track IDs `1` through `6`, changing bounding boxes/confidence values, UTC observation timestamps, and increasing visible durations (track `1` exceeded 70 seconds).
- Verified camera-failure handling with unavailable source `999`; the worker reported the unavailable source and exited cleanly before model loading.

### Deferred and remaining work

- Face recognition is deliberately postponed to a future phase; abnormal-condition detection does not require identity. The API keeps `recognized_identity` optional and `null`.
- Capture final normal/violation screenshots and demo video, then commit the completed work to Git.

### Next task

Load the custom pilot checkpoint in the live worker, remove the person-only filter, map the dataset class IDs, and test object-based observations such as `food_visible`, `missing_lab_coat`, and prohibited footwear.

## 2026-09-15 — Custom checkpoint live-worker integration

### Completed and locally verified

- Updated `Backend/scripts/rfdetr_live_webcam.py` to load `checkpoint_best_total.pth` by default, with an optional `RFDETR_CHECKPOINT` override.
- Removed the person-only detection filter and mapped the checkpoint's 12 one-based class IDs to its stored class names.
- Added direct policy-observation mapping: food, knife and handgun become `*_visible`; sandal and slipper become `prohibited_footwear`; permitted clothing and footwear remain visible-object observations.
- Kept the pilot confidence adjustable through `RFDETR_CONFIDENCE_THRESHOLD`, with `0.10` as the demonstration default because this tiny pilot checkpoint produces low scores.
- Static-image smoke check passed using `commons_25079653.jpg`: the custom checkpoint produced mapped `person` and `lab_coat` detections.
- Ruff and Python compilation checks passed.

### Next task

Run the updated live worker on the physical webcam and confirm that labels come from the pilot class set. Missing-attire observations remain pending because they require reliable person-to-clothing association and absence-over-time logic.

## 2026-09-16 — Custom live-tracker threshold fix

### Completed and locally verified

- Reproduced the live `Detections: 0` issue outside the webcam loop: the custom checkpoint returned six raw detections at threshold `0.10`, but ByteTrack returned zero tracks.
- Root cause: ByteTrack adds `0.10` to its configured activation threshold when starting a new track, while the pilot model's useful scores are currently around `0.10`–`0.15`.
- Aligned ByteTrack with `RFDETR_CONFIDENCE_THRESHOLD` and added a regression check for a `0.11` confidence detection.

### Next task

Run the live worker again and confirm a tracked box appears. The warnings about deprecated RF-DETR aliases and ByteTrack are library notices and do not stop detection.

## 2026-09-16 — Hybrid person and custom-object detection

### Completed and locally verified

- Confirmed the remaining zero-box webcam result was a pilot-model limitation rather than a camera, API, or tracker failure.
- On the same saved webcam frame, the pilot checkpoint produced weak duplicate scores around `0.10`–`0.15`, while pretrained RF-DETR Nano produced one person detection at `0.792`.
- Updated the live worker to use pretrained RF-DETR Nano for reliable person boxes and the custom checkpoint for non-person pilot classes, removing duplicate custom-person detections before ByteTrack.
- Static hybrid replay passed with one pretrained person, two custom non-person candidates, three merged detections, and three tracked detections.
- Physical webcam verification passed: one stable `person #1` track at `0.96` confidence, approximately `9.5 FPS`, and `105.2 ms` latency.

### Next task

Implement the three-second `missing_lab_coat` decision from a tracked person with no associated `lab_coat` or `lab_gown`, then verify the observation-to-dashboard flow. Treat it as an MVP demonstration until a larger `pilot_dataset_v2` improves custom-class reliability.

## 2026-09-16 — Three-second missing-lab-coat MVP

### Completed and locally verified

- Added person-to-attire association: a detected `lab_coat` or `lab_gown` counts as associated when its bounding-box center lies inside the tracked person's box.
- Added a per-track absence timer and `missing_lab_coat` overlay; the worker posts the derived observation only after three continuous seconds without associated attire.
- Kept detector observations separate from policy decisions: the worker posts an observation, and the existing FastAPI policy engine applies confidence, duration, and cooldown settings before creating an event.
- Reused real MySQL policy rule ID `4` (`Lab coat required`), enabled it, and set `min_duration_seconds` to `3.0`; its existing confidence threshold `0.5` and cooldown `60s` were preserved.
- Added focused attire-association and three-second API policy checks. Backend result: **8 passed**; Ruff and Python compilation checks passed.

### Next task

Run FastAPI and the live worker with observation posting enabled. Confirm that a tracked person without a detected coat shows `MISSING LAB COAT` after three seconds and creates a dashboard event. Then repeat while wearing a lab coat to assess the pilot model's false-alert rate.

## 2026-09-18 — Dashboard camera heartbeat and alert delivery fix

### Completed and locally verified

- Diagnosed the missing dashboard alert: policy rule ID `4` was disabled and the current detector process had posted zero `missing_lab_coat` observations.
- Re-enabled `Lab coat required` with its three-second duration, `0.5` confidence threshold, and `60s` cooldown.
- Made detector observation posting enabled by default; set `RFDETR_POST_OBSERVATIONS=0` only when a standalone local preview is intentionally required.
- Fixed the red camera indicator: `/cameras/status` now treats observations received within five seconds as the live detector heartbeat instead of competing with the worker for exclusive webcam access.
- Added automatic two-second dashboard polling for camera status and recent events.
- Backend result: **8 passed** and Ruff passed. Frontend lint, production build, and formatting checks passed.

### Next task

Restart the live worker so it loads the new posting default. Verify the camera card becomes green and a `missing_lab_coat` event appears automatically after three seconds without detected attire.

## 2026-09-22 — Camera safety and alert-timing baseline

### Completed and locally verified

- Removed the physical webcam fallback from `/api/v1/cameras/status`; dashboard polling now reports availability only from a detector observation received within the last five seconds.
- Added a regression test proving the status endpoint does not call OpenCV or activate the webcam when the detector is stopped.
- Preserved two-second frontend polling without allowing that polling to open camera hardware.
- Confirmed stored event ID `3` was created from a `missing_lab_coat` observation after `3.12s`; backend event creation occurred within the same database-recorded second.
- The dashboard can add up to `2s` because of its polling interval, giving a current evidence-based alert-display estimate of approximately `3.12s` to `5.12s` from the start of continuous missing-attire detection.
- Updated dashboard timestamps to `Asia/Kuala_Lumpur` using 24-hour formatting.
- Tuned live inference by moving observation posts off the camera loop and reusing detections between scheduled person/custom-model inference frames; a static benchmark measured approximately `15 FPS`.
- Verification passed: backend **9 tests**, Ruff, frontend lint, and frontend production build.

### Physical evidence still required

- Wear a lab coat in front of the physical webcam and confirm `lab_coat` or `lab_gown` is detected, `MISSING LAB COAT` clears, and no false alert is created.
- Record a stopwatch-based camera-to-dashboard delay for one fresh violation run; the stored timestamp result above is a baseline, not a physical display measurement.
- Capture final normal-state and violation-state screenshots plus a current end-to-end demo video. Existing `docs/day7-evidence` files predate this completed flow.

### Next task

Run the normal-attire physical test, then the fresh violation test. Save the screenshots/video under `docs/day7-evidence`, review the final diff, and commit only after those manual results are recorded.

## 2026-09-24 — Repeatable Missing Lab Coat demonstration hardening

### Completed and verified

- Added exact three-terminal setup and demonstration instructions to the backend and frontend READMEs.
- Verified the custom checkpoint's real class order and one-based prediction IDs using a saved pilot image: `1=person`, `2=lab_coat`.
- Updated the live worker so ByteTrack tracks people only; detected attire inherits the enclosing person's track ID instead of receiving an unrelated object track.
- Matched `lab_coat`/`lab_gown` to the same tracked person before clearing that person's missing-attire timer.
- Added focused tests for checkpoint mapping, person-only tracking, attire association, three-second confirmation, timer reset, observation payloads, and unavailable API handling.
- Improved the dashboard with two-second health/rule/event polling, readable Missing Lab Coat labels, pending/confirmed/false-alarm states, explicit review actions, retry/error messages, and Malaysia timestamps.
- Confirmed MySQL service availability and Alembic head `8b3e1c2a4d77`.
- Verified the real FastAPI-to-MySQL path with synthetic observation `1863` and event `29`; the clearly marked test event was reviewed as `false_alarm`.
- Verified webcam source `0` can open and capture one unsaved `640x480` frame, then releases successfully.
- Backend verification: **13 passed**, Ruff passed, and Python compilation passed.
- Frontend verification: lint, Prettier check, and production build passed.

### Manual physical demonstration still required

- Run the complete worker with a person in view and confirm a stable ByteTrack ID.
- Verify a detected lab coat/gown clears the timer and produces no new event.
- Verify no coat for three seconds produces the overlay, stored event, and React alert.
- Record current normal/violation screenshots, a stopwatch result, and an end-to-end demo video.

## 2026-10-01 — Pilot v2 checkpoint switch

- Prepared `datasets/pilot_dataset_v2/rfdetr`: 15 training images including all 11 new v2 images, 12 long-pants boxes; original v1 validation (2 images) and test (1 image) retained. All new session images stay in training to avoid session leakage.
- Fine-tuned Nano for 10 CUDA epochs from v1; saved `outputs/rfdetr_pilot_v2_20261001/checkpoint_best_total.pth`. Training configuration preserves all 12 category names.
- Live webcam default now loads this v2 checkpoint and prints its path. `RFDETR_CHECKPOINT` can still override it; clear old overrides before launching.
- Verification: 10 tracker tests and Ruff passed. Single-image test long-pants AP was 0.90; this tiny test is not generalisation evidence.
- Replayed three frames from the supplied USB-camera recording at clothing threshold 0.15. No long-pants detection survived in any frame; incorrect sandal, gown and handgun detections were also present. Saved raw results in `outputs/rfdetr_pilot_v2_20261001/video_replay.json`.
- V2 is active, but reliable trousers recognition remains incomplete. The 11 new images contain one participant/session wearing coat and trousers; add varied independent normal/no-coat/shorts examples and evaluate another training run before claiming a successful physical demo.
