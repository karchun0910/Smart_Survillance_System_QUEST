# Week 7 Webcam Setup Verification

Date started: 2026-08-25

Date completed: 2026-08-26

## Environment

Python 3.12.10 and OpenCV 4.14.0 were verified inside the Backend virtual
environment. Windows detected the NVIDIA GeForce RTX 3050 Laptop GPU with
4096 MiB of video memory. The NVIDIA driver reported CUDA capability.

## PyTorch GPU result

PyTorch `2.11.0+cu128` and Torchvision `0.26.0+cu128` are installed in the
Backend virtual environment. `torch.cuda.is_available()` returned `True`, and
the NVIDIA GeForce RTX 3050 Laptop GPU was detected successfully. RF-DETR Nano
also reported its inference device as `cuda`.

## Webcam result

OpenCV successfully opened laptop webcam source 0. The program displays a
mirrored 640 x 480 live feed with a timestamp and FPS counter. Lowercase Q
closes the program safely. The camera is released after closing and can be
opened again without being locked.

## Daily milestone

A stable Webcam -> OpenCV preview program is working.