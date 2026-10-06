import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from urllib.request import Request, urlopen

import cv2
import numpy as np
import supervision as sv
import torch
from rfdetr import RFDETRNano

FRAME_SIZE = (640, 480)
ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_PATH = Path(
    os.getenv(
        "RFDETR_CHECKPOINT",
        ROOT / "outputs" / "rfdetr_pilot_v2_20261001" / "checkpoint_best_total.pth",
    )
)
CONFIDENCE_THRESHOLD = float(os.getenv("RFDETR_CONFIDENCE_THRESHOLD", "0.35"))
PERSON_CONFIDENCE_THRESHOLD = float(os.getenv("RFDETR_PERSON_THRESHOLD", "0.50"))
PERSON_MODEL_INTERVAL = max(1, int(os.getenv("RFDETR_PERSON_INTERVAL", "3")))
CUSTOM_MODEL_INTERVAL = max(1, int(os.getenv("RFDETR_CUSTOM_INTERVAL", "8")))
MISSING_LAB_COAT_SECONDS = float(os.getenv("MISSING_LAB_COAT_SECONDS", "3"))
MISSING_LONG_PANTS_SECONDS = float(os.getenv("MISSING_LONG_PANTS_SECONDS", "3"))
PERSON_CLASS_ID = 1
PERSON_ATTIRE_CLASS_IDS = {2, 3, 4}
ATTIRE_LABELS = {"lab_coat", "lab_gown"}
WINDOW_NAME = "Smart Surveillance - RF-DETR"
POST_OBSERVATIONS = os.getenv("RFDETR_POST_OBSERVATIONS", "1") == "1"
API_URL = os.getenv("SURVEILLANCE_API_URL", "http://127.0.0.1:8000/api/v1")
CAMERA_ID = os.getenv("SURVEILLANCE_CAMERA_ID", "camera-0")
CAMERA_SOURCE = int(os.getenv("SURVEILLANCE_CAMERA_SOURCE", "1"))
OBSERVATION_LABELS = {
    "person": "person_present",
    "lab_coat": "lab_coat_visible",
    "lab_gown": "lab_gown_visible",
    "long_pants": "long_pants_visible",
    "shoe": "shoe_visible",
    "boot": "boot_visible",
    "sandal": "prohibited_footwear",
    "slipper": "prohibited_footwear",
    "food": "food_visible",
    "drink_container": "drink_container_visible",
    "knife": "knife_visible",
    "handgun": "handgun_visible",
}


def make_tracker() -> sv.ByteTrack:
    # ByteTrack adds 0.10 before activating a new track.
    return sv.ByteTrack(track_activation_threshold=0.0)


def merge_detections(
    person_detections: sv.Detections,
    custom_detections: sv.Detections,
) -> sv.Detections:
    custom_non_person = custom_detections[custom_detections.class_id != PERSON_CLASS_ID]
    return sv.Detections.merge(
        [
            person_detections[person_detections.class_id == PERSON_CLASS_ID],
            custom_non_person,
        ]
    )


def build_class_names(model_class_names: list[str]) -> dict[int, str]:
    expected = tuple(OBSERVATION_LABELS)
    actual = tuple(model_class_names)
    if actual != expected:
        raise RuntimeError(
            "Checkpoint class mapping does not match the pilot dataset: "
            f"expected {expected}, got {actual}"
        )
    return {class_id: name for class_id, name in enumerate(actual, start=1)}


def track_people_and_associate_objects(
    detections: sv.Detections,
    tracker: sv.ByteTrack,
) -> sv.Detections:
    people = tracker.update_with_detections(detections[detections.class_id == PERSON_CLASS_ID])
    if people.tracker_id is None:
        people.tracker_id = np.empty(0, dtype=int)
    objects = detections[detections.class_id != PERSON_CLASS_ID]
    object_track_ids = []
    for object_index, bbox in enumerate(objects.xyxy):
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        enclosing_people = [
            ((person[2] - person[0]) * (person[3] - person[1]), int(track_id))
            for person, track_id in zip(people.xyxy, people.tracker_id, strict=True)
            if person[0] <= center_x <= person[2] and person[1] <= center_y <= person[3]
        ]
        object_track_ids.append(
            min(enclosing_people)[1] if enclosing_people else -(object_index + 1)
        )
    objects.tracker_id = np.asarray(object_track_ids, dtype=int)
    return keep_best_person_attire(sv.Detections.merge([people, objects]))


def keep_best_person_attire(detections: sv.Detections) -> sv.Detections:
    if len(detections) == 0:
        detections.tracker_id = np.empty(0, dtype=int)
        return detections

    keep = [
        index
        for index, class_id in enumerate(detections.class_id)
        if int(class_id) not in PERSON_ATTIRE_CLASS_IDS
    ]
    best: dict[tuple[int, int], int] = {}
    for index, (class_id, track_id, confidence) in enumerate(
        zip(
            detections.class_id,
            detections.tracker_id,
            detections.confidence,
            strict=True,
        )
    ):
        class_id = int(class_id)
        track_id = int(track_id)
        if class_id not in PERSON_ATTIRE_CLASS_IDS or track_id <= 0:
            continue
        key = (track_id, class_id)
        if key not in best or confidence > detections.confidence[best[key]]:
            best[key] = index
    indices = np.asarray(sorted([*keep, *best.values()]), dtype=int)
    return detections[indices]


def find_people_missing_labels(
    detections: sv.Detections,
    class_names: dict[int, str],
    present_labels: set[str],
) -> dict[int, tuple[float, list[float]]]:
    present_track_ids = {
        int(track_id)
        for class_id, track_id in zip(
            detections.class_id,
            detections.tracker_id,
            strict=True,
        )
        if class_names.get(int(class_id)) in present_labels
    }
    missing: dict[int, tuple[float, list[float]]] = {}
    for bbox, class_id, track_id, confidence in zip(
        detections.xyxy,
        detections.class_id,
        detections.tracker_id,
        detections.confidence,
        strict=True,
    ):
        if class_names.get(int(class_id)) != "person":
            continue
        if int(track_id) not in present_track_ids:
            missing[int(track_id)] = (
                float(confidence),
                [float(value) for value in bbox],
            )
    return missing


def find_missing_lab_coats(
    detections: sv.Detections,
    class_names: dict[int, str],
) -> dict[int, tuple[float, list[float]]]:
    return find_people_missing_labels(detections, class_names, ATTIRE_LABELS)


def find_missing_long_pants(
    detections: sv.Detections,
    class_names: dict[int, str],
) -> dict[int, tuple[float, list[float]]]:
    return find_people_missing_labels(detections, class_names, {"long_pants"})


def update_missing_lab_coat_durations(
    missing_candidates: dict[int, tuple[float, list[float]]],
    missing_since: dict[int, float],
    frame_time: float,
) -> dict[int, float]:
    for track in set(missing_since) - set(missing_candidates):
        del missing_since[track]
    return {
        track: frame_time - missing_since.setdefault(track, frame_time)
        for track in missing_candidates
    }


def due_missing_observations(
    missing_candidates: dict[int, tuple[float, list[float]]],
    missing_durations: dict[int, float],
    last_posted: dict[tuple[int, str], float],
    frame_time: float,
    observation_label: str,
    required_seconds: float,
) -> list[tuple[int, float, list[float], float]]:
    return [
        (track, confidence, bbox, missing_durations[track])
        for track, (confidence, bbox) in missing_candidates.items()
        if missing_durations[track] >= required_seconds
        and frame_time - last_posted.get((track, observation_label), 0) >= 1
    ]


def due_missing_lab_coats(
    missing_candidates: dict[int, tuple[float, list[float]]],
    missing_durations: dict[int, float],
    last_posted: dict[tuple[int, str], float],
    frame_time: float,
) -> list[tuple[int, float, list[float], float]]:
    return due_missing_observations(
        missing_candidates,
        missing_durations,
        last_posted,
        frame_time,
        "missing_lab_coat",
        MISSING_LAB_COAT_SECONDS,
    )


def due_missing_long_pants(
    missing_candidates: dict[int, tuple[float, list[float]]],
    missing_durations: dict[int, float],
    last_posted: dict[tuple[int, str], float],
    frame_time: float,
) -> list[tuple[int, float, list[float], float]]:
    return due_missing_observations(
        missing_candidates,
        missing_durations,
        last_posted,
        frame_time,
        "missing_long_pants",
        MISSING_LONG_PANTS_SECONDS,
    )


def post_observation(
    track_id: int,
    label: str,
    confidence: float,
    bbox: list[float],
    duration_seconds: float,
) -> None:
    payload = {
        "camera_id": CAMERA_ID,
        "track_id": str(track_id),
        "label": OBSERVATION_LABELS.get(label, label),
        "confidence": confidence,
        "observed_at": datetime.now(UTC).isoformat(),
        "bbox": bbox,
        "model_version": f"rfdetr-nano-hybrid:{CHECKPOINT_PATH.name}",
        "duration_seconds": duration_seconds,
    }
    request = Request(
        f"{API_URL}/observations",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=0.25):
            pass
    except OSError:
        print("Observation API unavailable; continuing local preview.")


def main() -> None:
    if not CHECKPOINT_PATH.is_file():
        print(f"Checkpoint not found: {CHECKPOINT_PATH}")
        return

    print(f"Loading custom checkpoint: {CHECKPOINT_PATH}")
    custom_model = RFDETRNano.from_checkpoint(str(CHECKPOINT_PATH))
    custom_model.inference(
        compile=False,
        dtype=torch.float16,
        inplace=True,
    )
    person_model = RFDETRNano()
    person_model.inference(
        compile=False,
        dtype=torch.float16,
        inplace=True,
    )

    tracker = make_tracker()
    class_names = build_class_names(custom_model.class_names)

    camera = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY)
    if not camera.isOpened():
        camera.release()
        print(f"Could not open camera source {CAMERA_SOURCE}.")
        return

    print(f"Camera source {CAMERA_SOURCE} opened using {camera.getBackendName()}.")

    previous = perf_counter()
    frame_number = 0
    person_detections = sv.Detections.empty()
    custom_detections = sv.Detections.empty()
    last_posted: dict[tuple[int, str], float] = {}
    first_seen: dict[int, float] = {}
    missing_since: dict[int, float] = {}
    missing_long_pants_since: dict[int, float] = {}

    post_executor = ThreadPoolExecutor(max_workers=1)
    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("Could not capture a webcam frame.")
                break

            frame = cv2.resize(frame, FRAME_SIZE)
            frame = cv2.flip(frame, 1)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if frame_number % CUSTOM_MODEL_INTERVAL == 0:
                custom_detections = custom_model.predict(
                    rgb_frame,
                    threshold=CONFIDENCE_THRESHOLD,
                    include_source_image=False,
                )
            if frame_number % PERSON_MODEL_INTERVAL == 0:
                person_detections = person_model.predict(
                    rgb_frame,
                    threshold=PERSON_CONFIDENCE_THRESHOLD,
                    include_source_image=False,
                )
            frame_number += 1
            detections = merge_detections(person_detections, custom_detections)

            detections = track_people_and_associate_objects(detections, tracker)
            frame_time = perf_counter()
            visible_seconds = {
                int(track_id): frame_time - first_seen.setdefault(int(track_id), frame_time)
                for track_id in detections.tracker_id
            }
            missing_candidates = find_missing_lab_coats(detections, class_names)
            missing_durations = update_missing_lab_coat_durations(
                missing_candidates,
                missing_since,
                frame_time,
            )
            missing_long_pants_candidates = find_missing_long_pants(
                detections,
                class_names,
            )
            missing_long_pants_durations = update_missing_lab_coat_durations(
                missing_long_pants_candidates,
                missing_long_pants_since,
                frame_time,
            )

            if POST_OBSERVATIONS:
                for bbox, class_id, track_id, confidence in zip(
                    detections.xyxy.tolist(),
                    detections.class_id,
                    detections.tracker_id,
                    detections.confidence,
                    strict=True,
                ):
                    track = int(track_id)
                    label = class_names.get(int(class_id), f"class_{class_id}")
                    post_key = (track, label)
                    if frame_time - last_posted.get(post_key, 0) >= 1:
                        post_executor.submit(
                            post_observation,
                            track,
                            label,
                            float(confidence),
                            [float(value) for value in bbox],
                            visible_seconds[track],
                        )
                        last_posted[post_key] = frame_time

                for track, confidence, bbox, duration in due_missing_lab_coats(
                    missing_candidates,
                    missing_durations,
                    last_posted,
                    frame_time,
                ):
                    post_key = (track, "missing_lab_coat")
                    post_executor.submit(
                        post_observation,
                        track,
                        "missing_lab_coat",
                        confidence,
                        bbox,
                        duration,
                    )
                    last_posted[post_key] = frame_time

                for track, confidence, bbox, duration in due_missing_long_pants(
                    missing_long_pants_candidates,
                    missing_long_pants_durations,
                    last_posted,
                    frame_time,
                ):
                    post_key = (track, "missing_long_pants")
                    post_executor.submit(
                        post_observation,
                        track,
                        "missing_long_pants",
                        confidence,
                        bbox,
                        duration,
                    )
                    last_posted[post_key] = frame_time

            labels = []
            for class_id, track_id, confidence in zip(
                detections.class_id,
                detections.tracker_id,
                detections.confidence,
                strict=True,
            ):
                track = int(track_id)
                class_name = class_names.get(int(class_id), f"class_{class_id}")
                label = (
                    f"{class_name} #{track_id} {float(confidence):.2f} "
                    f"{visible_seconds[track]:.1f}s"
                )
                if class_name == "person" and track in missing_durations:
                    missing_duration = missing_durations[track]
                    if missing_duration >= MISSING_LAB_COAT_SECONDS:
                        label += " MISSING LAB COAT"
                    else:
                        label += f" no coat {missing_duration:.1f}/{MISSING_LAB_COAT_SECONDS:.0f}s"
                if class_name == "person" and track in missing_long_pants_durations:
                    missing_duration = missing_long_pants_durations[track]
                    if missing_duration >= MISSING_LONG_PANTS_SECONDS:
                        label += " MISSING LONG PANTS"
                    else:
                        label += (
                            f" no long pants {missing_duration:.1f}/"
                            f"{MISSING_LONG_PANTS_SECONDS:.0f}s"
                        )
                labels.append(label)

            annotated = sv.BoxAnnotator().annotate(
                frame.copy(),
                detections,
            )
            annotated = sv.LabelAnnotator().annotate(
                annotated,
                detections,
                labels,
            )

            now = perf_counter()
            elapsed = now - previous
            fps = 1.0 / elapsed if elapsed else 0.0
            previous = now

            cv2.putText(
                annotated,
                f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                annotated,
                (
                    f"Detections: {len(detections)} | Persons: "
                    f"{sum(int(class_id) == PERSON_CLASS_ID for class_id in detections.class_id)}"
                ),
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                annotated,
                (
                    f"Latency: {elapsed * 1000:.1f} ms | "
                    f"Thresholds P:{PERSON_CONFIDENCE_THRESHOLD:.2f} "
                    f"C:{CONFIDENCE_THRESHOLD:.2f}"
                ),
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow(WINDOW_NAME, annotated)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        post_executor.shutdown(wait=True)
        camera.release()
        cv2.destroyAllWindows()
        print("Camera released.")


if __name__ == "__main__":
    main()
