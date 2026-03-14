import base64
from pathlib import Path

from loguru import logger


def load_bytes_image(input_image_path: Path) -> bytes | None:
    try:
        with open(input_image_path, "rb") as f:
            image_bytes: bytes = f.read()
        return image_bytes
    except Exception as e:
        logger.error(f"Problems with reading bytes image!\n{e}")
        return None


def load_b64_and_encode(input_image_path: Path) -> str | None:
    """Load image, transform to base64, return as string"""
    try:
        if not input_image_path.exists():
            raise FileNotFoundError(f"Missing file:{input_image_path=}")
        return encode_image(input_image_path)
    except Exception as e:
        logger.error(f"Problems with encoding image!\n{e}")
        return None


def encode_image(image_path: Path) -> str:
    with open(image_path, "rb") as image_file:
        encoded_string: str = base64.b64encode(image_file.read()).decode("utf-8")
    logger.info(f"Encoded image: {image_path.name}")
    return encoded_string


def decode_b64_and_write(base64_string: str, output_image_path: Path) -> bool:
    """Check base64 string image, send to write or skip"""
    try:
        if output_image_path.exists():
            raise FileExistsError(f"Already file located at: {output_image_path=}")
        # TODO: check if base64_string is proper
        decode_image(base64_string, output_image_path)
        return True
    except Exception as e:
        logger.error(f"Problems with decoding image! {e}")
        return False


def decode_image(base64_string, image_path: Path) -> None:
    """Write base64 string to file"""
    raw_image: bytes = base64.b64decode(base64_string)
    with open(image_path, "wb") as image_file:
        image_file.write(raw_image)
    logger.info(f"Decoded image: {image_path.name}")
