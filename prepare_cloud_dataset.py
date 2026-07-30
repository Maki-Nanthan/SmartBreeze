import argparse
import zipfile
from pathlib import Path


DEFAULT_OUTPUT = "cloud_training_dataset.zip"
REQUIRED_PATHS = [
    Path("classroom_person.yaml"),
    Path("datasets/train/images"),
    Path("datasets/train/labels"),
    Path("datasets/valid/images"),
    Path("datasets/valid/labels"),
    Path("datasets/test/images"),
    Path("datasets/test/labels"),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a zip file for cloud YOLO training."
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output zip path.")
    return parser.parse_args()


def check_dataset():
    missing = [path for path in REQUIRED_PATHS if not path.exists()]
    if missing:
        missing_list = "\n".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing required dataset paths:\n{missing_list}")


def add_path(zip_file, path):
    if path.is_file():
        zip_file.write(path, path.as_posix())
        return

    for file_path in path.rglob("*"):
        if file_path.is_file():
            zip_file.write(file_path, file_path.as_posix())


def main():
    args = parse_args()
    output_path = Path(args.output)

    check_dataset()

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path in REQUIRED_PATHS:
            add_path(zip_file, path)

    print(f"Cloud training dataset created: {output_path}")


if __name__ == "__main__":
    main()
