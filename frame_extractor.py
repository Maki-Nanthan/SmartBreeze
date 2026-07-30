import cv2
import os

VIDEO_EXTENSIONS = (".mp4", ".avi", ".mov", ".mkv")
DEFAULT_LABEL = "UNLABELED"

def extract_frames(video_path, output_dir, label, sample_rate_sec=1):
    # Create output folder
    os.makedirs(os.path.join(output_dir, label), exist_ok=True)

    cap = cv2.VideoCapture(video_path)

    fps = int(cap.get(cv2.CAP_PROP_FPS))

    if fps == 0:
        print(f"Could not read: {video_path}")
        return

    frame_interval = int(fps * sample_rate_sec)

    count = 0
    saved_count = 0

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            break

        if count % frame_interval == 0:
            filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_{saved_count:04d}.jpg"

            save_path = os.path.join(output_dir, label, filename)

            cv2.imwrite(save_path, frame)

            saved_count += 1

        count += 1

    cap.release()

    print(f"Done: {video_path} -> {saved_count} frames")

def process_video_folder(raw_video_dir, output_dir):
    found_videos = False

    for item in os.listdir(raw_video_dir):
        item_path = os.path.join(raw_video_dir, item)

        if os.path.isdir(item_path):
            label = item

            for video in os.listdir(item_path):
                if video.lower().endswith(VIDEO_EXTENSIONS):
                    video_path = os.path.join(item_path, video)
                    extract_frames(video_path, output_dir, label)
                    found_videos = True

        elif item.lower().endswith(VIDEO_EXTENSIONS):
            extract_frames(item_path, output_dir, DEFAULT_LABEL)
            found_videos = True

    if not found_videos:
        print(f"No videos found in: {raw_video_dir}")


# ----------------------------
# Automatically process videos
# ----------------------------

RAW_VIDEO_DIR = "videos"
OUTPUT_DIR = "datasets"

process_video_folder(RAW_VIDEO_DIR, OUTPUT_DIR)
