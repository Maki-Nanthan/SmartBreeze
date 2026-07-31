import argparse
import zipfile
from pathlib import Path


DEFAULT_OUTPUT = "cloud_training_dataset.zip"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = [
    PROJECT_ROOT / "data_science" / "classroom_person.yaml",
    PROJECT_ROOT / "datasets" / "train" / "images",
    PROJECT_ROOT / "datasets" / "train" / "labels",
    PROJECT_ROOT / "datasets" / "valid" / "images",
    PROJECT_ROOT / "datasets" / "valid" / "labels",
    PROJECT_ROOT / "datasets" / "test" / "images",
    PROJECT_ROOT / "datasets" / "test" / "labels",
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


def archive_name(path):
    if path.name == "classroom_person.yaml":
        return "classroom_person.yaml"
    return path.relative_to(PROJECT_ROOT).as_posix()


def add_path(zip_file, path):
    if path.is_file():
        zip_file.write(path, archive_name(path))
        return

    for file_path in path.rglob("*"):
        if file_path.is_file():
            zip_file.write(file_path, archive_name(file_path))


def main():
    args = parse_args()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    check_dataset()

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path in REQUIRED_PATHS:
            add_path(zip_file, path)

    print(f"Cloud training dataset created: {output_path}")


if __name__ == "__main__":
    main()
