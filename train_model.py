import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fine-tune YOLO on the classroom person detection dataset."
    )
    parser.add_argument("--data", default="classroom_person.yaml", help="YOLO dataset YAML.")
    parser.add_argument("--model", default="yolo11n.pt", help="Starting YOLO weights.")
    parser.add_argument("--epochs", type=int, default=20, help="Training epochs.")
    parser.add_argument("--imgsz", type=int, default=640, help="Training image size.")
    parser.add_argument("--batch", type=int, default=4, help="Batch size. Lower this on slow machines.")
    parser.add_argument("--device", default="cpu", help="Use 'cpu' or GPU device like '0'.")
    parser.add_argument("--project", default=None, help="Optional training output folder.")
    parser.add_argument("--name", default="classroom_person_detector", help="Run name.")
    return parser.parse_args()


def main():
    args = parse_args()

    data_path = Path(args.data)
    model_path = Path(args.model)

    if not data_path.exists():
        raise FileNotFoundError(f"Dataset config not found: {data_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Starting model not found: {model_path}")

    model = YOLO(str(model_path))
    train_options = {
        "data": str(data_path),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "workers": 0,
        "name": args.name,
        "exist_ok": True,
    }

    if args.project:
        train_options["project"] = args.project

    model.train(**train_options)

    best_model = Path(model.trainer.save_dir) / "weights" / "best.pt"
    print(f"Training finished. Best model: {best_model}")
    print("Use it with:")
    print(f"python edge_demo.py --model \"{best_model}\" --video \"videos/HIGH.MOV\"")


if __name__ == "__main__":
    main()
