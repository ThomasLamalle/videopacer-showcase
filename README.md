# VideoPacer

Times race runners from a finish-line video instead of chips: it finds the bibs, reads the numbers and gives each runner a finish time, live, on a phone. Work in progress prototype, written in Rust.

![A real run on a 5K finish: bib numbers, the race clock read from the video and a results list that fills as runners cross](assets/demo.gif)

*A real run on a 20 s test clip of the Angels on the Run 5K (2026), one where every bib and every finish time is right: the number on each bib, the race time read from the clock beside the line, and each finish time as the runner crosses.*

## Results

17 clips from real races, 8 to 30 s each and 5 minutes in all, labelled by hand and never used in training.

| | |
|---|---|
| Bibs found | 92% (172 of 187) |
| Finish times within 2 s | 89% (166 of 187) |
| Wrong numbers | 3.7% (7 of 187 a run on average) |
| Speed | about 33 frames per second on 4 CPU cores, no GPU: faster than a 30 fps camera |

## Stack

Each camera runs the whole pipeline itself. A server only merges the results of several cameras and is never in the frame loop. Android first, then PC and iPhone.

- **Computer vision:** small YOLO-family bib detector, PP-OCR-style digit reader, models trained on bibs and exported to ONNX (int8 and fp32), OpenCV.
- **Core:** Rust, ONNX Runtime on CPU, frame-by-frame streaming with bounded memory, tracking that lets the detector run on every other frame, mostly around known runners, speed benchmarked in frames per second.
- **App:** Tauri 2 shell for Android, embedded web review page and leaderboard, race clock read from the video.
- **Tooling:** hand-labelled ground truth with automated scoring, GitHub Actions (self-hosted runner, APK build), models and datasets on Hugging Face.

## Code

The source is private while the project is in progress. Happy to walk through it or share access.

Contact: [LinkedIn](https://www.linkedin.com/in/thomas-lamalle-4a358b94/)

Site: https://thomaslamalle.github.io/videopacer-showcase/
