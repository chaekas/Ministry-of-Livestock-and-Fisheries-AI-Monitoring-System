"""Download the published fish-detector ONNX model into the local models directory.

Review the model card, license, and suitability for your data before use.
"""
from pathlib import Path

from huggingface_hub import hf_hub_download

REPO_ID = "akridge/yolo11-fish-detector-grayscale"
REVISION = "ee89537a26ba73122c1ca99c58ff23a91b361fda"
FILENAME = "yolo11n-fish-detector-grayscale.onnx"
DESTINATION = Path("models") / "fish_counting.onnx"


def main() -> None:
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    downloaded = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        revision=REVISION,
    )
    source = Path(downloaded)
    DESTINATION.write_bytes(source.read_bytes())
    print(f"Fish model saved to: {DESTINATION}")
    print("This model targets grayscale underwater footage; validate it on representative images.")


if __name__ == "__main__":
    main()
