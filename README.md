# VideoPacer

Times race runners from a finish-line video instead of chips: it finds the bibs, reads the numbers and gives each runner a finish time, live, on a phone. Work in progress prototype, written in Rust.

![Bibs detected on a finish line with a live race clock and leaderboard](assets/demo.gif)

*Honolulu Marathon 2014 footage: detected bibs, race clock read from the video, live leaderboard.*

## Results

17 clips of 15 s from real races, labelled by hand and never used in training.

| | |
|---|---|
| Bibs found | 175 of 187 |
| Finish times within 2 s | 170 of 187 |
| Speed | 2.1x real time on 4 CPU cores, no GPU |

## Stack

Each camera runs the whole pipeline itself. A server only merges the results of several cameras and is never in the frame loop. Android first, then PC and iPhone.

- **Computer vision:** small YOLO-family bib detector, PP-OCR-style digit reader, models trained on bibs and exported to ONNX (int8 and fp32), OpenCV.
- **Core:** Rust, ONNX Runtime on CPU, frame-by-frame streaming with bounded memory, speed benchmarked in real-time multiples.
- **App:** Tauri 2 shell for Android, embedded web review page and leaderboard, race clock read from the video.
- **Tooling:** hand-labelled ground truth with automated scoring, GitHub Actions (self-hosted runner, APK build), models and datasets on Hugging Face.

## Code

The source is private while the project is in progress. Happy to walk through it or share access.

Contact: [LinkedIn](https://www.linkedin.com/in/thomas-lamalle-4a358b94/)

Site: https://thomaslamalle.github.io/videopacer-showcase/
