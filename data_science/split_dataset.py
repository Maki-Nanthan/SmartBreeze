import os
import random
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Dataset paths
image_dir = PROJECT_ROOT / "datasets" / "images"
label_dir = PROJECT_ROOT / "datasets" / "labels"

output_dir = PROJECT_ROOT / "datasets"

# Split ratio
train_ratio = 0.70
valid_ratio = 0.20
test_ratio = 0.10

# Get all images
images = list(image_dir.glob("*.jpg"))
random.shuffle(images)

total = len(images)

train_end = int(total * train_ratio)
valid_end = train_end + int(total * valid_ratio)

train_images = images[:train_end]
valid_images = images[train_end:valid_end]
test_images = images[valid_end:]


def copy_files(image_list, split):

    (output_dir / split / "images").mkdir(parents=True, exist_ok=True)
    (output_dir / split / "labels").mkdir(parents=True, exist_ok=True)

    for image in image_list:

        label = label_dir / f"{image.stem}.txt"

        shutil.copy(image, output_dir / split / "images" / image.name)

        if label.exists():
            shutil.copy(label, output_dir / split / "labels" / label.name)


copy_files(train_images, "train")
copy_files(valid_images, "valid")
copy_files(test_images, "test")

print("Dataset split completed!")
print(f"Train : {len(train_images)}")
print(f"Valid : {len(valid_images)}")
print(f"Test  : {len(test_images)}")
