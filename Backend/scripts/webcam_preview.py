from datetime import datetime
from time import perf_counter

import cv2

FRAME_SIZE = (640, 480)
WINDOW_NAME = "Smart Surveillance Webcam"


def main() -> None:
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError("Could not open webcam source 0.")

    previous_frame_time = perf_counter()

    try:
        while True:
            frame_captured, frame = camera.read()

            if not frame_captured:
                print("Could not capture a webcam frame.")
                break

            frame = cv2.resize(frame, FRAME_SIZE)
            frame = cv2.flip(frame, 1)

            current_frame_time = perf_counter()
            elapsed = current_frame_time - previous_frame_time
            fps = 1.0 / elapsed if elapsed > 0 else 0.0
            previous_frame_time = current_frame_time

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cv2.putText(
                frame,
                timestamp,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"FPS: {fps:.1f}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow(WINDOW_NAME, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Camera released.")


if __name__ == "__main__":
    main()
