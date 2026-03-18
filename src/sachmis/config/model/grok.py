from loguru import logger

from sachmis.utils.print import printer

from .family import ModelFamily

# IMPORTANT: Last update: 18.03.2026


class Groks(ModelFamily):
    G2 = "g2"
    G4 = "g4"
    G41N = "g41fn"
    G41R = "g41f"
    G420M = "g420"
    G420N = "g42n"
    G420R = "g42r"
    GCF1 = "gcf1"

    # LATER: implement:
    # - grok-imagine-video
    # - Realtime API, text and audio ($3/hour)
    # - Text to Speech

    @property
    def category_unique(self) -> str:
        """Used for pydantic Models -> str -> Models and for CLI"""
        return "x"

    @property
    def api_name(self) -> str:
        return {
            Groks.G2: "grok-2-image-1212",
            Groks.G4: "grok-4",
            Groks.G41N: "grok-4-1-fast-non-reasoning",
            Groks.G41R: "grok-4-1-fast-reasoning",
            Groks.G420M: "grok-4.20-multi-agent-experimental-beta-0304",
            Groks.G420N: "grok-4.20-experimental-beta-0304-non-reasoning",
            Groks.G420R: "grok-4.20-experimental-beta-0304-reasoning",
            Groks.GCF1: "grok-code-fast-1",
        }[self]

    @property
    def token_price(self) -> dict[str, float]:
        """Price list depending on model"""
        # TODO: price increase for high volume prompt
        # TODO: check batch api prices and usage (half price)
        fast: dict[str, float] = {"input": 0.2, "cached": 0.05, "output": 0.5}
        code: dict[str, float] = {"input": 0.2, "cached": 0.02, "output": 1.5}
        main: dict[str, float] = {"input": 3.0, "cached": 0.75, "output": 15}
        image: dict[str, float] = {"input": 2.0, "cached": 0, "output": 10}
        g420: dict[str, float] = {"input": 2.0, "cached": 0.2, "output": 6}
        match self:
            case Groks.G41R | Groks.G41N:
                return fast
            case Groks.GCF1:
                return code
            case Groks.G4:
                return main
            case Groks.G2:
                return image
            case Groks.G420M | Groks.G420N | Groks.G420R:
                return g420

    @staticmethod
    def match_token(token_name: str) -> str:
        """Match from response token name to price list token name"""
        assignment: dict[str, str] = {
            # TODO: grok token
            # - total token and other token summary
            # - image token
            # - problem with repeated conversations, check logfiles
            # "totalTokens" =None,
            # "promptTokens"=None,
            "promptTextTokens": "input",
            "cachedPromptTextTokens": "cached",
            "completionTokens": "output",
            "reasoningTokens": "output",
            # TODO: Function calls
        }
        return assignment.get(token_name, "")

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

        printer(f"{total_cost=}")

        return total_cost  # LATER: return dataclass or so
