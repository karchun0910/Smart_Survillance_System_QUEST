import json

import numpy as np
import pytest
import supervision as sv

from scripts import rfdetr_live_webcam
from scripts.rfdetr_live_webcam import (
    build_class_names,
    due_missing_lab_coats,
    due_missing_long_pants,
    find_missing_lab_coats,
    find_missing_long_pants,
    make_tracker,
    merge_detections,
    post_observation,
    track_people_and_associate_objects,
    update_missing_lab_coat_durations,
)


def test_pilot_threshold_can_start_a_track() -> None:
    detections = sv.Detections(
        xyxy=np.array([[10, 10, 100, 100]], dtype=float),
        confidence=np.array([0.11]),
        class_id=np.array([1]),
    )

    tracked = make_tracker().update_with_detections(detections)

    assert len(tracked) == 1


def test_pretrained_person_replaces_weak_custom_person() -> None:
    person_detections = sv.Detections(
        xyxy=np.array([[10, 10, 100, 100]], dtype=float),
        confidence=np.array([0.90]),
        class_id=np.array([1]),
    )
    custom_detections = sv.Detections(
        xyxy=np.array([[12, 12, 98, 98], [20, 20, 80, 80]], dtype=float),
        confidence=np.array([0.11, 0.12]),
        class_id=np.array([1, 2]),
    )

    merged = merge_detections(person_detections, custom_detections)

    assert merged.class_id.tolist() == [1, 2]
    assert merged.confidence.tolist() == [0.90, 0.12]


def test_checkpoint_class_mapping_matches_pilot_dataset() -> None:
    expected = list(rfdetr_live_webcam.OBSERVATION_LABELS)

    assert build_class_names(expected) == {
        class_id: name for class_id, name in enumerate(expected, start=1)
    }

    with pytest.raises(RuntimeError, match="Checkpoint class mapping"):
        build_class_names(["person", "long_pants", "lab_coat"])


def test_only_people_are_tracked_and_coat_uses_person_track_id() -> None:
    detections = sv.Detections(
        xyxy=np.array([[0, 0, 100, 200], [20, 20, 80, 150]], dtype=float),
        confidence=np.array([0.95, 0.80]),
        class_id=np.array([1, 2]),
    )

    associated = track_people_and_associate_objects(detections, make_tracker())

    assert associated.tracker_id[0] > 0
    assert associated.tracker_id.tolist() == [
        associated.tracker_id[0],
        associated.tracker_id[0],
    ]
    assert find_missing_lab_coats(associated, {1: "person", 2: "lab_coat"}) == {}


def test_empty_frame_returns_empty_detections() -> None:
    associated = track_people_and_associate_objects(
        sv.Detections.empty(),
        make_tracker(),
    )

    assert len(associated) == 0
    assert associated.tracker_id.tolist() == []
    assert find_missing_lab_coats(associated, {1: "person"}) == {}
    assert find_missing_long_pants(associated, {1: "person"}) == {}


def test_duplicate_attire_boxes_keep_only_the_best_per_person() -> None:
    detections = sv.Detections(
        xyxy=np.array(
            [
                [0, 0, 100, 200],
                [10, 10, 90, 180],
                [15, 15, 85, 175],
                [200, 10, 250, 180],
            ],
            dtype=float,
        ),
        confidence=np.array([0.95, 0.80, 0.60, 0.70]),
        class_id=np.array([1, 2, 2, 2]),
    )

    associated = track_people_and_associate_objects(detections, make_tracker())

    assert associated.class_id.tolist() == [1, 2]
    assert associated.confidence.tolist() == [0.95, 0.80]


def test_only_person_without_associated_coat_is_missing() -> None:
    detections = sv.Detections(
        xyxy=np.array(
            [
                [0, 0, 100, 200],
                [20, 20, 80, 150],
                [200, 0, 300, 200],
            ],
            dtype=float,
        ),
        confidence=np.array([0.95, 0.80, 0.90]),
        class_id=np.array([1, 2, 1]),
        tracker_id=np.array([1, 1, 3]),
    )

    missing = find_missing_lab_coats(detections, {1: "person", 2: "lab_coat"})

    assert list(missing) == [3]
    assert missing[3][0] == 0.90
    assert missing[3][1] == [200.0, 0.0, 300.0, 200.0]


def test_missing_lab_coat_is_due_after_three_seconds_and_resets() -> None:
    candidate = {7: (0.91, [0.0, 0.0, 100.0, 200.0])}
    missing_since: dict[int, float] = {}
    last_posted: dict[tuple[int, str], float] = {}

    assert update_missing_lab_coat_durations(candidate, missing_since, 10.0) == {7: 0.0}
    durations = update_missing_lab_coat_durations(candidate, missing_since, 13.0)
    assert due_missing_lab_coats(candidate, durations, last_posted, 13.0) == [
        (7, 0.91, [0.0, 0.0, 100.0, 200.0], 3.0)
    ]

    last_posted[(7, "missing_lab_coat")] = 13.0
    assert due_missing_lab_coats(candidate, durations, last_posted, 13.5) == []
    durations = update_missing_lab_coat_durations(candidate, missing_since, 14.0)
    assert due_missing_lab_coats(candidate, durations, last_posted, 14.0) == [
        (7, 0.91, [0.0, 0.0, 100.0, 200.0], 4.0)
    ]
    assert update_missing_lab_coat_durations({}, missing_since, 14.5) == {}
    assert missing_since == {}


def test_missing_long_pants_is_associated_timed_and_reset() -> None:
    without_pants = sv.Detections(
        xyxy=np.array([[0, 0, 100, 200]], dtype=float),
        confidence=np.array([0.92]),
        class_id=np.array([1]),
        tracker_id=np.array([5]),
    )
    with_pants = sv.Detections(
        xyxy=np.array([[0, 0, 100, 200], [10, 80, 90, 195]], dtype=float),
        confidence=np.array([0.92, 0.81]),
        class_id=np.array([1, 4]),
        tracker_id=np.array([5, 5]),
    )
    class_names = {1: "person", 4: "long_pants"}
    missing_since: dict[int, float] = {}
    last_posted: dict[tuple[int, str], float] = {}

    candidate = find_missing_long_pants(without_pants, class_names)
    assert update_missing_lab_coat_durations(candidate, missing_since, 10.0) == {5: 0.0}
    durations = update_missing_lab_coat_durations(candidate, missing_since, 13.0)
    assert due_missing_long_pants(candidate, durations, last_posted, 13.0) == [
        (5, 0.92, [0.0, 0.0, 100.0, 200.0], 3.0)
    ]

    visible = find_missing_long_pants(with_pants, class_names)
    assert visible == {}
    assert update_missing_lab_coat_durations(visible, missing_since, 14.0) == {}
    assert missing_since == {}


def test_post_observation_payload_and_api_failure(monkeypatch, capsys) -> None:
    requests = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    def capture(request, timeout):
        requests.append((request, timeout))
        return Response()

    monkeypatch.setattr(rfdetr_live_webcam, "urlopen", capture)
    post_observation(7, "missing_lab_coat", 0.91, [0, 0, 100, 200], 3.0)

    payload = json.loads(requests[0][0].data)
    assert requests[0][1] == 0.25
    assert payload["track_id"] == "7"
    assert payload["label"] == "missing_lab_coat"
    assert payload["duration_seconds"] == 3.0

    def unavailable(_request, timeout):
        assert timeout == 0.25
        raise OSError("offline")

    monkeypatch.setattr(rfdetr_live_webcam, "urlopen", unavailable)
    post_observation(7, "missing_lab_coat", 0.91, [0, 0, 100, 200], 4.0)
    assert "continuing local preview" in capsys.readouterr().out
