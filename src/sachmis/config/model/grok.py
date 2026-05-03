from loguru import logger

from .family import ModelFamily

# NEXT: Last update: 18.03.2026


class Groks(ModelFamily):
    G43 = "g43"
    G420M = "g420"
    G420N = "g42n"
    G420R = "g42r"
    G4 = "g4"
    G2 = "g2"
    GCF1 = "gcf1"

    # LATER: implement:
    # - grok-imagine-video
    # - Realtime API, text and audio ($3/hour)
    # - Text to Speech

    @property
    def unique_letter(self) -> str:
        """Used for pydantic Models -> str -> Models and for CLI"""
        return "x"

    @property
    def target(self) -> str:
        """Identifier for FileUploader"""
        return "xai"

    @property
    def api_name(self) -> str:
        return {
            Groks.G43: "grok-4.3",
            Groks.G420M: "grok-4.20-multi-agent",
            Groks.G420N: "grok-4.20-non-reasoning",
            Groks.G420R: "grok-4.20-reasoning",
            Groks.G4: "grok-4",
            Groks.G2: "grok-2-image-1212",
            Groks.GCF1: "grok-code-fast-1",
        }[self]

    @property
    def token_price(self) -> dict[str, float]:
        """Price list depending on model"""
        # TODO: price increase for high volume prompt
        # TODO: check batch api prices and usage (half price)
        code: dict[str, float] = {"input": 0.2, "cached": 0.02, "output": 1.5}
        main: dict[str, float] = {"input": 3.0, "cached": 0.75, "output": 15}
        image: dict[str, float] = {"input": 2.0, "cached": 0, "output": 10}
        # x2 for >200k
        g43: dict[str, float] = {"input": 1.25, "cached": 0.2, "output": 2.5}
        match self:
            case Groks.GCF1:
                return code
            case Groks.G4:
                return main
            case Groks.G2:
                return image
            case Groks.G420M | Groks.G420N | Groks.G420R | Groks.G43:
                return g43

    def usage_cost(self, token_usage: dict[str, int]) -> float:
        """Calculates usage from 1 response"""

        price_list: dict[str, float] = self.token_price

        total_cost = 0
        sst_prompt_token = 0
        cached_token = 0
        output_token = 0

        # TODO: Function calls

        for usage_name, n_token in token_usage.items():
            match usage_name:
                case "totalTokens":
                    xai_total_token: int = n_token
                    continue

                case "promptTokens":
                    xai_prompt_token: int = n_token
                    continue

                case "promptTextTokens":
                    token_price: float = price_list["input"]
                    sst_prompt_token += n_token

                case "cachedPromptTextTokens":
                    token_price: float = price_list["cached"]
                    cached_token += n_token

                case "completionTokens":
                    token_price: float = price_list["output"]
                    output_token += n_token

                case "reasoningTokens":
                    token_price: float = price_list["output"]
                    output_token += n_token

                case _:
                    logger.warning(f"Unknown token_usage: {usage_name=}")
                    logger.warning(f"probably server side tool: {n_token=}")
                    continue

            total_cost += token_price * n_token / 1_000_000

        sst_total_token: int = sst_prompt_token + output_token

        logger.info(f"{sst_total_token=}")
        logger.info(f"{xai_total_token=}")
        logger.info(f"{sst_prompt_token=}")
        logger.info(f"{xai_prompt_token=}")
        logger.info(f"{cached_token=}")

        # TODO: move to printer?
        print(f"{total_cost=}")

        return total_cost  # LATER: return dataclass or so
