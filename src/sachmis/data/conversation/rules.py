from enum import StrEnum, auto


class PromptTransitionRules(StrEnum):
    """Prompt: Number of inputs always constant, usually 1.
    Number of ancestors usually constant (Resend exactly same Prompt).
    Special Prompt has multiple fathers and for each 1 grandchild.
    Internally stores the information to bridge Pre/Post Responses."""

    REGULAR = auto()
    ROOT = auto()
    MULTI = auto()

    def description(self) -> str:
        return {
            self.REGULAR: "Base Prompt: 1 Ancestor, n Successors",
            self.ROOT: "RootPrompt with 0 Ancestors, n Successors",
            self.MULTI: "Special Prompt with at least 1 symmetric mux-demux ancestor",
        }[self]

    @classmethod
    def explain(cls) -> str:
        raise NotImplementedError

    def valid_ancestor(self, response: ResponseTransitionRules) -> bool:
        match self:
            case self.REGULAR:
                return response in {
                    ResponseTransitionRules.REGULAR,
                    ResponseTransitionRules.BACKWARD,
                }
            case self.MULTI:
                return response in {
                    ResponseTransitionRules.FORWARD,
                    ResponseTransitionRules.BIDIRECT,
                }
            case self.ROOT:
                return False

    def valid_successor(self, response: ResponseTransitionRules) -> bool:
        match self:
            case self.REGULAR:
                return response in {
                    ResponseTransitionRules.REGULAR,
                    ResponseTransitionRules.FORWARD,
                }
            case self.ROOT:  # same as regular
                return response in {
                    ResponseTransitionRules.REGULAR,
                    ResponseTransitionRules.FORWARD,
                }
            case self.MULTI:
                return response in {
                    ResponseTransitionRules.BIDIRECT,
                    ResponseTransitionRules.BACKWARD,
                }


class ResponseTransitionRules(StrEnum):
    """Response: Number of inputs always constant, usually 1.
    Number of ancestors usually grows (continue on successful Response)
    Forward Demux Response with q siblings: all point to same Prompt.
    Backward Mux Response with q siblings: all pointed from same Prompt.
    Bidirect Response is (independent) Forward and Backward together."""

    REGULAR = auto()
    FORWARD = auto()
    BACKWARD = auto()
    BIDIRECT = auto()

    def description(self) -> str:
        return {
            self.REGULAR: "Base Response with 1 Ancestor , n ancestors",
            self.FORWARD: "Demux Response with 1 Ancestor, q ancestor 1 grandchild",
            self.BACKWARD: "Mux Response with q predecessor, 1 ancestor 1 grandchild",
            self.BIDIRECT: "Response with q1 predecessor, q2 ancestor 1 grand(child and father)",
        }[self]

    @classmethod
    def explain(cls) -> str:
        raise NotImplementedError

    def valid_ancestor(self, prompt: PromptTransitionRules) -> bool:
        match self:
            case self.REGULAR:
                return prompt in {
                    PromptTransitionRules.REGULAR,
                    PromptTransitionRules.ROOT,
                }
            case self.FORWARD:
                return prompt in {
                    PromptTransitionRules.REGULAR,
                    PromptTransitionRules.ROOT,
                }
            case self.BACKWARD:
                return prompt in {
                    PromptTransitionRules.MULTI,
                }
            case self.BIDIRECT:
                return prompt in {
                    PromptTransitionRules.MULTI,
                }

    def valid_successor(self, prompt: PromptTransitionRules) -> bool:
        match self:
            case self.REGULAR:
                return prompt in {
                    PromptTransitionRules.REGULAR,
                }
            case self.FORWARD:
                return prompt in {
                    PromptTransitionRules.MULTI,
                }
            case self.BACKWARD:
                return prompt in {
                    PromptTransitionRules.REGULAR,
                }
            case self.BIDIRECT:
                return prompt in {
                    PromptTransitionRules.MULTI,
                }
