"""Draw the showcase demo: a run's boxes, numbers and finish times over its video, with a results sheet beside it.

It writes assets/demo.mp4 for the page, assets/demo.jpg as its poster and assets/demo.gif for the README.

To make it again, on the VPS:
1. Run the pipeline on the clip, from the VideoPacer repository:
     ./target/release/videopacer videos/sample2/video.mp4 <run folder>
2. Get the two fonts, Red Hat Display and Red Hat Text:
     curl -sSL -o <fonts>/display.ttf "https://github.com/google/fonts/raw/main/ofl/redhatdisplay/RedHatDisplay%5Bwght%5D.ttf"
     curl -sSL -o <fonts>/text.ttf "https://github.com/google/fonts/raw/main/ofl/redhattext/RedHatText%5Bwght%5D.ttf"
3. Draw it (needs ffmpeg). 870 is the last frame: the tracks still open at the end of the clip are cut at 898.
     uv run --with pillow scripts/render_demo.py <video.mp4> <run folder>/summary.json <fonts> assets 870
"""
import json
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

video, summary, fonts, assets, last = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
out = f"{assets}/demo.mp4"
run = json.load(open(summary))

SCALE = 0.6
VW, VH = 1152, 648          # the footage, at SCALE of 1920x1080
COL = 300                   # the results sheet on the right
W, H = VW + COL, VH
RATE = 30000 / 1001
COBALT, INK, GREY, RULE = (39, 71, 255), (0, 0, 0), (95, 99, 104), (228, 230, 234)


def font(name, size, weight):
    face = ImageFont.truetype(f"{fonts}/{name}.ttf", size)
    face.set_variation_by_axes([weight])
    return face


TAG = font("display", 15, 800)
SMALL = font("text", 13, 600)
LABEL = font("text", 14, 500)
CLOCK = font("display", 40, 800)
BIB = font("display", 19, 800)
TIME = font("text", 16, 500)
PLACE = font("text", 14, 500)
NUM = ["tnum"]

tracks = [t for t in run["tracks"] if t["best_bib"]]
boxes = {t["track_id"]: {b[0]: b[1:5] for b in t["boxes"]} for t in tracks}
finishers = sorted((t for t in tracks if t["finish_frame"] is not None and t["finish_frame"] <= last),
                   key=lambda t: t["finish_frame"])
offset = run["clock"]["offset_seconds"]
clock_box = [v * SCALE for v in run["clock"]["bbox"]]


def short(time):
    """08:00:50.1 as 8:00:50.1."""
    return time[1:] if time.startswith("0") else time


def race_time(frame):
    seconds = offset + frame / RATE
    return f"{int(seconds // 3600)}:{int(seconds % 3600 // 60):02}:{seconds % 60:04.1f}"


def tag(pen, text, face, fill, ink, left, bottom, alpha=255):
    """A label with its bottom left corner here, kept inside the footage."""
    width = pen.textlength(text, font=face, features=NUM) + 10
    x, y = min(left, VW - width), max(bottom - 20, 0)
    pen.rounded_rectangle([x, y, x + width, y + 20], 3, fill=fill + (alpha,))
    pen.text((x + 5, y + 10), text, font=face, fill=ink + (alpha,), anchor="lm", features=NUM)


def box(pen, rect, colour, alpha=255):
    left, top, width, height = (v * SCALE for v in rect)
    shape = [left - 2, top - 2, left + width + 2, top + height + 2]
    pen.rounded_rectangle([shape[0] - 1, shape[1] - 1, shape[2] + 1, shape[3] + 1], 4, outline=(0, 0, 0, alpha // 3), width=1)
    pen.rounded_rectangle(shape, 3, outline=colour + (alpha,), width=2)
    return shape


def overlay(frame):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pen = ImageDraw.Draw(layer)
    # Where the race time is read: the clock on the gantry.
    x, y, w, h = clock_box
    pen.rounded_rectangle([x, y, x + w, y + h], 4, outline=(255, 255, 255, 230), width=2)
    tag(pen, "Race clock", SMALL, (255, 255, 255), INK, x, y + h + 24)
    # The finish line of this clip is the bottom edge of the picture: two rows of black and white tiles, drawn a little
    # above it so that they show.
    tile, top = 8, VH - 28
    for along in range(VW // tile + 1):
        for across in (0, 1):
            colour = (0, 0, 0) if (along + across) % 2 else (255, 255, 255)
            pen.rectangle([along * tile, top + across * tile, along * tile + tile - 1, top + across * tile + tile - 1],
                          fill=colour + (255,))
    tag(pen, "Finish line", SMALL, (255, 255, 255), INK, 10, top - 4)
    for t in tracks:
        finish = t["finish_frame"]
        rect = boxes[t["track_id"]].get(frame)
        if rect and (finish is None or frame <= finish):
            shape = box(pen, rect, (255, 255, 255))
            tag(pen, t["best_bib"], TAG, (255, 255, 255), INK, shape[0], shape[1] - 3)
        # A runner who just finished keeps a cobalt box with the time for a second, fading out.
        if finish is not None and finish <= last and 0 <= frame - finish < 40:
            alpha = 255 if frame - finish < 20 else int(255 * (40 - (frame - finish)) / 20)
            shape = box(pen, boxes[t["track_id"]][finish], COBALT, alpha)
            tag(pen, f"{t['best_bib']}  {short(t['finish_time'])}", TAG, COBALT, (255, 255, 255), shape[0], shape[1] - 3, alpha)
    return layer


def sheet(canvas, frame):
    """The results sheet: the race time read from the video, then each finisher as they cross."""
    pen = ImageDraw.Draw(canvas)
    x0 = VW
    pen.rectangle([x0, 0, W, H], fill=(255, 255, 255))
    pen.text((x0 + 22, 22), "Race clock, read from the video", font=LABEL, fill=GREY)
    pen.text((x0 + 22, 42), race_time(frame), font=CLOCK, fill=INK, features=NUM)
    pen.line([x0 + 22, 104, W - 22, 104], fill=RULE, width=1)
    done = [t for t in finishers if t["finish_frame"] <= frame]
    rows = 15
    shown = list(enumerate(done, 1))[-rows:]
    for line, (place, t) in enumerate(shown):
        y = 112 + line * 34
        age = frame - t["finish_frame"]
        if age < 45:
            # The newest row lights up and fades back to white.
            tint = 1 - age / 45
            pen.rectangle([x0 + 10, y, W - 10, y + 32], fill=tuple(int(255 - (255 - c) * 0.14 * tint) for c in COBALT))
        pen.text((x0 + 44, y + 17), str(place), font=PLACE, fill=GREY, anchor="rm", features=NUM)
        pen.text((x0 + 58, y + 17), t["best_bib"], font=BIB, fill=COBALT if age < 45 else INK, anchor="lm", features=NUM)
        pen.text((W - 22, y + 17), short(t["finish_time"]), font=TIME, fill=INK, anchor="rm", features=NUM)
        pen.line([x0 + 22, y + 33, W - 22, y + 33], fill=RULE, width=1)


decode = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={VW}:{VH}:flags=lanczos",
                           "-frames:v", str(last + 1), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
encode = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", "30000/1001", "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "27",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", out], stdin=subprocess.PIPE)
for frame in range(last + 1):
    raw = decode.stdout.read(VW * VH * 3)
    if len(raw) < VW * VH * 3:
        break
    canvas = Image.new("RGBA", (W, H))
    canvas.paste(Image.frombytes("RGB", (VW, VH), raw), (0, 0))
    canvas = Image.alpha_composite(canvas, overlay(frame))
    sheet(canvas, frame)
    if frame == 700:
        canvas.convert("RGB").save(f"{assets}/demo.jpg", quality=80)
    encode.stdin.write(canvas.convert("RGB").tobytes())
encode.stdin.close()
encode.wait()
# The README's GIF: 12 s from 8 s in, small enough for GitHub to show.
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "8", "-t", "12", "-i", out, "-vf",
                "fps=8,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];"
                "[b][p]paletteuse=dither=none:diff_mode=rectangle", f"{assets}/demo.gif"], check=True)
print("frames", frame + 1, "finishers", len(finishers))
