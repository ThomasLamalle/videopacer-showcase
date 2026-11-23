# VideoPacer

Times race runners from a finish-line video instead of chips: it finds the bibs, follows them, reads the numbers and gives each runner a finish time. Rust, built to run on a phone: each camera device runs the whole pipeline itself, and a server only merges passages.

![Bibs detected and read on a finish line](assets/demo.gif)

*Honolulu Marathon 2014 finish line. Boxes come from the bib detector, the number above each box is the vote of its track.*

## Results

17 ground-truth clips of 15 s from real races, labelled by hand, never used in training.

| | |
|---|---|
| Bibs found | 175 of 187 |
| Finish times within 2 s | 170.5 of 187 (mean of 2 runs) |
| Wrong numbers | 8.5 a run, mostly flagged for review |
| Speed | 2.1x real time on 4 CPU cores, no GPU |

## How it works

frame, then bib detector (640 px, 30 a second), then a reader on each box, then tracks by association, then a vote on the number, then a passage at the finish line.

- **Tracks, not a vote between numbers.** A reader that drops a digit does it on the same bib, so inside one track the wrong reading just loses the vote.
- **The number is the most likely source of the readings.** A reader drops a digit far more often than it adds one.
- **Look past the line.** Bib errors fell from 36 to 27 and one sample from 8 errors to 1.
- **A race list of bibs is optional**, and never used in tests: a list of the few bibs in a sample would be cheating.

## Engineering story

- **Rebuilt from scratch, one reviewed piece at a time.** The first pipeline grew too complex to maintain, so the core restarted from empty files. One idea per pull request, each with the ground-truth numbers before and after and a one-page explanation of the logic.
- **Core and cosmetic changes.** Anything that can change a number in a result is reviewed by a human, and must be a rule that holds for any race, never a fix for one bib of one video. The rest merges when checks pass. CI runs the ground-truth check on every pull request and fails when more bibs are missed.
- **Measure before believing.** One run is noisy by up to 4 bibs depending on which frames the detector sees, so each video runs at two time offsets. Replays are quick but over-promise, so ideas are confirmed with a full run.
- **Prefer removing a mechanism to adding one.** Partial readings voting for every race number containing them found a few bibs but invented many wrong ones (12.5 missed and 27 wrong, against 15.5 and 10 before), so it was dropped.
- **Speed is measured honestly.** Video decoding is never counted. A change under review runs the detector at 15 a second and reads on the frame halfway between: 34 % less time (2.14x to 1.41x real time) for 2 more missed bibs. Missed bibs come first, so that trade is for the reviewer to decide.

## Stack

Rust, ONNX Runtime, OpenCV, a small YOLO-family bib detector and a tiny PP-OCR-style digit reader trained on bibs, a Tauri 2 shell for Android, GitHub Actions.

## Code

The source repository is private for now. The code and the explanation pages of each change are available on request.
