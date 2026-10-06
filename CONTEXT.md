# Smart Surveillance System Domain

This glossary defines the project language for laboratory monitoring. It separates what computer vision observes from what laboratory policy decides.

## Video and identity

**Tracked person**:
A person-shaped subject followed across video frames by a track identifier. A tracked person is not automatically a known student.
_Avoid_: Student, user (unless identity has been confirmed)

**Recognized user**:
A tracked person matched by the senior face-recognition module with an accepted confidence threshold.
_Avoid_: Certain identity, guaranteed identity

**Camera zone**:
A configured region or line in a camera view where a policy applies, such as an entrance, bench or restricted area.
_Avoid_: Area (when the geometry matters)

**Track**:
The time-bounded identity continuity for one tracked person, including first seen, last seen, location and duration.
_Avoid_: Permanent identity

## Observations and events

**Observation**:
A timestamped, confidence-scored statement produced by a vision module, such as `person_present`, `missing_long_pants`, `food_visible` or `running`.
_Avoid_: Violation (an observation is not yet a policy decision)

**Candidate event**:
A temporary policy match that still needs duration, cooldown or confidence confirmation.
_Avoid_: Alarm

**Confirmed event**:
A candidate event that passes the configured policy thresholds and is stored for notification and review.
_Avoid_: Proof of wrongdoing

**Evidence item**:
A limited snapshot or short clip linked to a confirmed event for lecturer review.
_Avoid_: Continuous recording

**Review decision**:
An authorised lecturer's disposition of a confirmed event, such as confirmed, false alarm or needs follow-up.
_Avoid_: Automatic final judgement

## Policy and safety

**Laboratory policy rule**:
An editable condition that maps observations and context—camera, zone, time, confidence, duration and severity—to an event decision.
_Avoid_: Hard-coded model behaviour

**Hazard class**:
A project-defined object category whose risk level is configured by laboratory policy. The model detects the category; policy determines whether it is dangerous in context.
_Avoid_: Object is inherently dangerous

**Rule version**:
The immutable rule snapshot used when an event is evaluated, retained so a later rule edit cannot rewrite history.
_Avoid_: Current rule (when discussing past events)

**Abnormal action**:
A selected time-based activity that is not allowed in a configured laboratory context, such as eating, running or unsafe handling.
_Avoid_: Universal abnormality
