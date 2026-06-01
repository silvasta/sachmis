from loguru import logger

from ..config.models import DummyFamily, Geminis, Groks, ModelFamily


# MOVE: as function of config.model?
def model_from_unique(model_unique: str) -> ModelFamily | None:
    """Transform model unique str back to ModelFamily Enum"""

    try:
        if len(parts := model_unique.split("-")) != 2:
            logger.error(f"'{model_unique=}' must be 'prefix-name'")
            return None

        family, model_name = parts

    except Exception as e:
        logger.error(f"String operation failure for {model_unique=}:\n{e}")
        return None

    match family:
        case "x":
            target_enum: type[ModelFamily] = Groks
        case "g":
            target_enum: type[ModelFamily] = Geminis
        case "d":
            target_enum: type[ModelFamily] = DummyFamily
        case _:
            logger.error("ModelFamily can't be identified by input {family=}")
            return None

    try:
        model: ModelFamily = target_enum(model_name)

    except ValueError:
        logger.error(f"{model_name=} is no member of {target_enum.__name__}")
        return None

    return model


def parse_raw_models(raw_models: list[str]) -> list[ModelFamily]:
    """Parse all models, ignore raw_models that fail parsing"""
    return [
        parsed_model
        for model_unique in raw_models
        if (parsed_model := model_from_unique(model_unique))  #
        is not None
    ]


if __name__ == "__main__":
    """Just to play around"""
    tests = [
        "x-g420",
        "g-g3",
    ]
    for test in tests:
        result: ModelFamily | None = model_from_unique(test)
        print(result)
