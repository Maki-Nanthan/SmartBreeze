from ultralytics import YOLO
from pathlib import Path

# ----------------------------------------------------
# Load pretrained YOLO11 Nano model
# ----------------------------------------------------
model = YOLO("yolo11n.pt")

# ----------------------------------------------------
# Dataset folders
# ----------------------------------------------------
image_folder = Path("datasets/images")
label_folder = Path("datasets/labels")

# Create labels folder if it doesn't exist
label_folder.mkdir(parents=True, exist_ok=True)

# Supported image formats
image_extensions = ["*.jpg", "*.jpeg", "*.png"]

# ----------------------------------------------------
# Loop through all images
# ----------------------------------------------------
for ext in image_extensions:
    for image_path in image_folder.glob(ext):

        # Run inference
        results = model(image_path)

        # Original image size
        height, width = results[0].orig_shape

        # Output label file
        label_path = label_folder / f"{image_path.stem}.txt"

        with open(label_path, "w") as f:

            # Process every detected object
            for box in results[0].boxes:

                # COCO class ID
                cls = int(box.cls[0])

                # Keep ONLY PERSON (class 0)
                if cls != 0:
                    continue

                # Bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0]

                # Convert to YOLO format
                x_center = ((x1 + x2) / 2) / width
                y_center = ((y1 + y2) / 2) / height
                box_width = (x2 - x1) / width
                box_height = (y2 - y1) / height

                # Save label
                f.write(
                    f"0 "
                    f"{x_center:.6f} "
                    f"{y_center:.6f} "
                    f"{box_width:.6f} "
                    f"{box_height:.6f}\n"
                )

        print(f"✅ Processed: {image_path.name}")

print("\n🎉 Auto-labeling completed successfully!")