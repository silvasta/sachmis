from loguru import logger

from sachmis.config.model import Geminis, Groks, ModelFamily


def reversed_name_from_unique(model_unique: str) -> ModelFamily | None:
    """Transform model unique str back to ModelFamily Enum"""

    try:
        family, model_name = model_unique.split("-")

        match family:
            case "x":
                model = Groks(model_name)
            case "g":
                model = Geminis(model_name)
            case _:
                raise AttributeError("ModelFamily can't be identified")

        return model

    except Exception as e:
        logger.warning(f"Unable to parse: {model_unique=}")
        logger.error(e)

    return None


if __name__ == "__main__":
    tests = [
        "x-g2",
        "x-g420",
        "xx-ff",
        "c-44-44",
        "c",
        "g-g3",
        "g-gg",
    ]
    for test in tests:
        result: ModelFamily | None = reversed_name_from_unique(test)
        print(result)
