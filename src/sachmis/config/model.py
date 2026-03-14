from abc import ABCMeta, abstractmethod
from ..utils.print import printer
from enum import Enum, EnumMeta


# INFO: this is basically a Model param file for external fixed data

# REFACTOR: Use csv instead of Enum?
# - needs factory for Enum or Literal for typer

# REFACTOR: params in config, calculations to data!


class AbstractEnum(ABCMeta, EnumMeta):
    """This is enough to use ABC in Enum
    Usage:
    class MyABCEnum(Enum, metaclass=AbstractEnum):
    """


class ModelFamil(Enum, metaclass=AbstractEnum):
    """Define general properties for models of all companies"""

    @property
    def topicality(self) -> str:  # TODO: don't forget update!
        """Last update of price list, token names or new models"""
        return "21.01.2026"

    @property
    @abstractmethod
    def api_name(self) -> str:
        """Full name that is used for API call"""
        raise NotImplementedError(f"Missing state transission validation for: {self}")

    @property
    @abstractmethod
    def category_unique(self) -> str:
        """Unique bidirectional identifier for model category (company)"""
        raise NotImplementedError(f"Missing category_unique for class: {type[self]}")

    @property
    def unique(self) -> str:
        """Unique bidirectional identifier for single model"""
        return f"{self.category_unique}-{self.value}"


class Geminis(Models):
    G3 = "g3"
    G3I = "g3i"
    G3F = "g3f"

    @property
    def category_unique(self) -> str:
        """Used for pydantic, Models -> str -> Models and for CLI"""
        return "g"

    @property
    def api_name(self) -> str:
        return {
            self.G3: "gemini-3-pro-preview",
            self.G3F: "gemini-3-flash-preview",
            self.G3I: "gemini-3-pro-image-preview",
        }[self]


class Groks(Models):
    G41FR = "g41f"
    G41FNR = "g41fn"
    GCF1 = "gcf1"
    G4FR = "g4f"
    G4FNR = "g4fn"
    G4 = "g4"
    G2 = "g2"

    @property
    def category_unique(self) -> str:
        """Used for pydantic Models -> str -> Models and for CLI"""
        return "x"

    @property
    def api_name(self) -> str:
        return {
            Groks.G41FR: "grok-4-1-fast-reasoning",
            Groks.G41FNR: "grok-4-1-fast-non-reasoning",
            Groks.GCF1: "grok-code-fast-1",
            Groks.G4FR: "grok-4-fast-reasoning",
            Groks.G4FNR: "grok-4-fast-non-reasoning",
            Groks.G4: "grok-4",
            Groks.G2: "grok-2-image-1212",
        }[self]

    @property
    def can_reasoning(self) -> bool:
        """Model has reasoning abilities"""
        return self not in {Groks.G41FNR, Groks.G4FNR, Groks.G2}

    @property
    def can_image(self) -> bool:
        """Model can create images"""
        return self in {Groks.G2}

    @property
    def token_names(self):
        """Token names from response"""
        token: list[str] = [
            "totalTokens",
            "promptTokens",
            "promptTextTokens",
            "cachedPromptTextTokens",
            "completionTokens",
        ]
        if self.can_reasoning:
            token += ["reasoningTokens"]
        if self.can_image:
            token += ["imageTokens"]
        return token

    @property
    def token_price(self) -> dict[str, float]:
        """Price list depending on model"""
        # prices from 20.11.25, price for 1 million token (confirmed 21.01.25)
        fast: dict[str, float] = {"input": 0.2, "cached": 0.05, "output": 0.5}
        code: dict[str, float] = {"input": 0.2, "cached": 0.02, "output": 1.5}
        main: dict[str, float] = {"input": 3.0, "cached": 0.75, "output": 15}
        image: dict[str, float] = {"input": 2.0, "cached": 0, "output": 10}
        match self:
            case Groks.G41FR | Groks.G41FNR | Groks.G4FR | Groks.G4FNR:
                return fast
            case Groks.GCF1:
                return code
            case Groks.G4:
                return main
            case Groks.G2:
                return image

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

    def usage_cost(self, token_usage: dict[str, int]) -> tuple[float, int]:
        """Calculates usage from 1 response"""
        # TODO: check all token names and rewrite
        # TODO: Function calls
        price_list: dict[str, float] = self.token_price
        total_cost = 0
        total_token = 0
        for token_name in self.token_names:
            if token_name == "totalTokens":
                print(f"total token from list: {token_usage[token_name]}")
            elif token_name == "promptTokens":
                print(f"prompt token from list: {token_usage[token_name]}")
            else:
                price_category: str = self.match_token(token_name)
                token_price: float = price_list[price_category]
                token: int = token_usage.get(token_name, 0)
                if token_name == "promptTextTokens":
                    cached_text_token: int = token_usage.get(
                        "cachedPromptTextTokens", 0
                    )
                    print(f"prompt text token from list: {token}")
                    print(f"cached text token from list: {cached_text_token}")
                    token -= cached_text_token
                cost: float = token_price * token / 1_000_000
                total_cost += cost
                total_token += token
        printer.print(f"{total_token=}")
        printer.print(f"{total_cost=}")
        return total_cost, total_token
