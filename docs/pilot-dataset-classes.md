# Pilot Dataset Classes

This document defines the object classes used for the pilot Smart Surveillance dataset.

Dataset labels describe objects that are visibly present in an image. Labels such as
`missing_lab_coat`, `missing_long_pants` and `food_visible` are backend observations,
not CVAT annotation classes.

## Final Pilot Class List

1. `person`
2. `lab_coat`
3. `lab_gown`
4. `long_pants`
5. `shoe`
6. `boot`
7. `sandal`
8. `slipper`
9. `food`
10. `drink_container`
11. `knife`
12. `handgun`

The class `dangerous_object` must not be used because it is too vague. Each prohibited
object must have its own visible and clearly defined class.

## Class Definitions

### `person`

A visible human body or visible part of a human body that can be identified as a person.

### `lab_coat`

A protective, front-opening coat worn over normal clothing during laboratory work. It
normally has long sleeves and extends to the thighs or knees.

Include laboratory coats that are clearly worn by a person.

Exclude ordinary jackets, hoodies, shirts, aprons and coats that are not laboratory
protective clothing.

### `lab_gown`

A loose protective laboratory garment that covers the torso and is worn over normal
clothing. It may close at the front or back.

Include protective laboratory gowns that are clearly worn by a person.

Exclude graduation robes, dressing gowns, raincoats and ordinary loose clothing.

### `long_pants`

A lower-body garment with two separate leg sections that covers the person from the
waist or hips to approximately the ankles.

Include jeans, trousers, track pants, work pants and protective laboratory trousers
that clearly cover both legs.

Exclude shorts, knee-length pants, skirts, dresses and clothing where the leg coverage
cannot be determined from the image.

The label describes the visible garment only. The backend later determines whether
the person's clothing satisfies the laboratory policy.

### `shoe`

Footwear that encloses the foot and toes, with its upper section ending at or below
the ankle.

Include closed-toe sneakers, formal shoes, work shoes and safety shoes.

Exclude boots, sandals, slippers, socks without shoes and bare feet.

### `boot`

Footwear that encloses the foot and extends above the ankle.

Include safety boots, work boots and other closed protective boots.

Exclude ordinary shoes, sandals and slippers.

The dataset records the visible footwear type. Laboratory policy treats `shoe` and
`boot` as permitted footwear.

### `sandal`

Open footwear with a sole held to the foot by straps, while leaving a noticeable
portion of the toes, sides or heel exposed.

Include strapped sandals and open-toe footwear secured around the foot or ankle.

Exclude closed shoes, boots, loose slippers, slides and flip-flops.

### `slipper`

Loose, casual footwear that does not fully enclose or securely protect the foot.

Include house slippers, slides and flip-flops.

Exclude closed shoes, boots and sandals that are secured around the foot or ankle.

The dataset records the visible footwear type. Laboratory policy treats `sandal` and
`slipper` as prohibited footwear.

### `food`

A visible edible item or prepared meal intended for human consumption.

Include meals, snacks, fruit, bread and clearly identifiable packaged food intended
for immediate consumption.

Exclude empty food packaging, laboratory samples, culture media, medicine and objects
that cannot be confidently identified as food.

### `drink_container`

A personal container intended to hold a beverage.

Include drinking bottles, cups, mugs, beverage cans and takeaway drink containers,
whether open or closed.

Exclude laboratory glassware, chemical bottles, medicine containers and containers
whose purpose cannot be determined from the image.

The dataset detects `food` and `drink_container` objects. Actions such as eating or
drinking belong to the later action-recognition phase and are not annotation classes
in this object-detection dataset.

### `knife`

A clearly visible handheld cutting tool with a blade and handle.

Include kitchen knives, pocket knives and utility knives when the blade or overall
knife shape is identifiable.

Exclude scissors, screwdrivers, laboratory scalpels and objects whose blade or handle
cannot be identified confidently.

### `handgun`

A clearly visible handheld firearm-shaped object with the appearance of a pistol or
revolver.

Include approved dataset images and harmless replicas that clearly resemble a handgun.

Exclude phones, drills, tools, vague object shapes and toys that do not visually
resemble a handgun.

The labels `knife` and `handgun` describe visible object categories. The backend policy
engine determines whether their presence creates a prohibited-object event.

## Class Examples

- `person`: A student standing or walking inside the laboratory.
- `lab_coat`: A white, long-sleeved laboratory coat worn over normal clothing.
- `lab_gown`: A blue or white protective laboratory gown covering the torso.
- `long_pants`: Ankle-length jeans, trousers or work pants.
- `shoe`: A closed-toe sneaker, formal shoe or safety shoe ending below the ankle.
- `boot`: A closed safety boot extending above the ankle.
- `sandal`: Open-toe footwear secured using straps.
- `slipper`: A slide, flip-flop or loose house slipper.
- `food`: A sandwich, fruit, meal or clearly identifiable packaged snack.
- `drink_container`: A drinking bottle, cup, mug or beverage can.
- `knife`: An approved image of a kitchen knife or a harmless knife replica.
- `handgun`: An approved image of a handgun or a harmless realistic replica.

## Annotation Rules

### Partially Visible Objects

Annotate a partially visible object only when its class can still be identified
confidently.

Draw the bounding box tightly around the visible part of the object. Do not estimate
or invent the object's hidden boundaries.

If an object extends outside the image, end the bounding box at the image boundary.

If another object blocks part of it, use CVAT's `occluded` option when available.

Do not annotate a small or unclear fragment when its class cannot be determined
confidently.

### Overlapping Objects

Annotate every identifiable object separately, even when their bounding boxes overlap.

Do not merge two people or two objects into one bounding box.

When two people overlap, create a separate `person` box for each person whose body can
still be identified.

Clothing and footwear boxes may appear inside a person's bounding box. For example, one
person may have separate `person`, `lab_coat`, `long_pants` and `shoe` annotations.

A carried object, such as a `drink_container`, must have its own box even when it
overlaps the person's hand or body.

Mark the object behind another object as `occluded` when CVAT provides that option.

### Minimum Object Size

For a 640 × 480 image, annotate an object only when its visible bounding box is at
least 16 pixels wide and 16 pixels high.

The object must also contain enough visible detail for its class to be identified
confidently.

Do not enlarge a bounding box merely to satisfy the minimum size.

If an important object is too small, capture another image with the object closer to
the camera instead of annotating the unclear object.

For images with a different resolution, scale the 16 × 16-pixel minimum
proportionally.

## Image Naming Format

Use this format for every captured image:

`pilot_<scenario>_<lighting>_<distance>_<angle>_<date>_<sequence>.jpg`

Rules:

- Use lowercase letters only.
- Use underscores instead of spaces.
- Use the date format `YYYYMMDD`.
- Use a four-digit sequence number starting from `0001`.
- Keep the same filename when copying an image from `raw_images` to
  `selected_images`.

Allowed values:

- Scenario: `normal` or `violation`
- Lighting: `bright`, `normal` or `dim`
- Distance: `near`, `medium` or `far`
- Angle: `front`, `left`, `right` or `high`

Example:

`pilot_normal_bright_medium_front_20260830_0001.jpg`

## Planned Capture Scenarios

| ID | Type | Scenario | Expected annotations |
|---|---|---|---|
| N01 | Normal | One person wearing a lab coat, long pants and closed shoes | `person`, `lab_coat`, `long_pants`, `shoe` |
| N02 | Normal | One person wearing a lab gown, long pants and safety boots | `person`, `lab_gown`, `long_pants`, `boot` |
| N03 | Normal | Two correctly dressed people standing together | Two `person` boxes and the visible clothing and footwear boxes |
| N04 | Normal | Empty laboratory with no people or controlled objects | No annotations |
| V01 | Violation | Person without a lab coat or lab gown | `person` and any other visible classes; the backend infers missing protective clothing |
| V02 | Violation | Person wearing shorts and sandals | `person`, `sandal`; the backend infers missing long pants |
| V03 | Violation | Person wearing slippers | `person`, `slipper` |
| V04 | Violation | Food and a personal drink container on a laboratory table | `food`, `drink_container` |
| V05 | Violation | Person holding a harmless knife replica or using an approved image | `person`, `knife` |
| V06 | Violation | Harmless handgun replica or approved handgun image | `handgun`, plus `person` when visible |

Capture both positive and negative examples. A violation image may intentionally have
no annotation for a required item because the backend detects its absence from the
available observations.

## Lighting, Distance and Camera-Angle Plan

Use `normal` lighting, `medium` distance and a `front` camera angle as the baseline.
Change only one condition at a time so its effect can be evaluated clearly.

| Test | Lighting | Distance | Angle |
|---|---|---|---|
| Baseline | Normal room lighting | Medium: approximately 1–2 metres | Front |
| Bright lighting | Bright | Medium | Front |
| Dim lighting | Dim but still visibly usable | Medium | Front |
| Near distance | Normal | Near: approximately 0.5–1 metre | Front |
| Far distance | Normal | Far: approximately 2–3 metres | Front |
| Left angle | Normal | Medium | Approximately 45° left |
| Right angle | Normal | Medium | Approximately 45° right |
| High angle | Normal | Medium | Camera positioned above eye level |

Capture at least one `normal` image and one `violation` image for every test condition.

Complete darkness is excluded because the laptop webcam does not have night-vision
hardware. Record this as a known hardware limitation rather than a failed dataset
scenario.

## Privacy and Participant-Consent Controls

### Before Capturing Images

- Obtain informed written consent from every identifiable participant.
- Explain the project purpose, the images being collected, how they will be used,
  where they will be stored and who may access them.
- Explain whether selected images will be uploaded to CVAT Online.
- Obtain separate explicit consent before using images for face recognition.
- Do not include minors without formal guardian consent and university approval.
- Capture images in a controlled area and prevent non-consenting bystanders from
  entering the frame.

### Participant Identification

- Assign each participant a private code such as `participant_001`.
- Do not place names, student IDs, email addresses or phone numbers in image filenames.
- Store consent records separately from images and annotations.
- Do not commit consent forms or identifiable raw images to Git.

### Storage and Access

- Limit access to the student researcher and authorised supervisor.
- Protect the CVAT account and local computer against unauthorised access.
- Upload only selected, consented images to CVAT.
- Do not share dataset files publicly without participant and university approval.
- Do not upload identifiable images to third-party services unless the consent notice
  and university approval cover that service.

### Retention and Deletion

- Keep personal images only while they are required for the stated FYP purpose.
- Delete rejected raw images after the image-selection and quality-review process.
- Define and record a deletion date for selected images, annotations and exports.
- Permanently delete dataset copies when they are no longer required.
- Keep a simple record of what was deleted and when.

### Withdrawal

- Tell participants how they can withdraw their consent.
- Use the participant code to locate and delete their images and annotations.
- Stop using withdrawn images in future training, testing and demonstrations.

These controls support the project but do not replace university ethics approval,
supervisor instructions or applicable legal requirements.

## Policy Mapping

The dataset records visible objects. The backend policy engine decides whether the
objects satisfy laboratory rules.

- `lab_coat` and `lab_gown` can both satisfy the protective-garment requirement.
- `shoe` and `boot` are treated as permitted footwear.
- `sandal` and `slipper` are treated as prohibited footwear.
- `food` and `drink_container` can produce food-or-drink observations.
- `knife` and `handgun` can produce prohibited-object observations.


Only approved images or harmless replicas may be used for the `knife` and `handgun`
classes.