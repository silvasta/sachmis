from enum import StrEnum, auto


class PromptTypes(StrEnum):  # IMPORTANT: PromptEdges?
    REGULAR = auto()
    ROOT = auto()
    MULTI = auto()

    def description(self) -> str:
        return {
            self.REGULAR: "Base Prompt: 1 Ancestor, n Successors",
            self.ROOT: "RootPrompt with 0 Ancestors, n Successors",
            self.MULTI: "Special Prompt with at least 1 symmetric mux-demux ancestor",
        }[self]

    def explain(self) -> str:
        return """Prompt: Number of inputs always constant, usually 1.
        Number of ancestors usually constant (Resend exactly same Prompt).
        Special Prompt has multiple fathers and for each father 1 grandchild.
        Internally stores the information to bridge Pre/Post Responses.
        """

    def valid_ancestor(self, response: ResponseTypes) -> bool:
        match self:
            case self.REGULAR:
                return response in {
                    ResponseTypes.REGULAR,
                    ResponseTypes.BACKWARD,
                }
            case self.MULTI:
                return response in {
                    ResponseTypes.FORWARD,
                    ResponseTypes.BIDIRECT,
                }
            case self.ROOT:
                return False

    def valid_successor(self, response: ResponseTypes) -> bool:
        match self:
            case self.REGULAR:
                return response in {
                    ResponseTypes.REGULAR,
                    ResponseTypes.FORWARD,
                }
            case self.ROOT:  # same as regular
                return response in {
                    ResponseTypes.REGULAR,
                    ResponseTypes.FORWARD,
                }
            case self.MULTI:
                return response in {
                    ResponseTypes.BIDIRECT,
                    ResponseTypes.BACKWARD,
                }


class ResponseTypes(StrEnum):  # IMPORTANT: ResponseEdges?
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

    def explain(self) -> str:
        return """Response: Number of inputs always constant, usually 1.
        Number of ancestors usually growing (Continue on Successful Response).
        Forward Demux Response with q siblings: all point forward to same Prompt.
        Backward Mux Response with q siblings: all pointed backwards from same Prompt.
        Bidirect Response is when Forward and Backward (independent) happens in same Response.
        """

    def valid_ancestor(self, prompt: PromptTypes) -> bool:
        match self:
            case self.REGULAR:
                return prompt in {
                    PromptTypes.REGULAR,
                    PromptTypes.ROOT,
                }
            case self.FORWARD:
                return prompt in {
                    PromptTypes.REGULAR,
                    PromptTypes.ROOT,
                }
            case self.BACKWARD:
                return prompt in {
                    PromptTypes.MULTI,
                }
            case self.BIDIRECT:
                return prompt in {
                    PromptTypes.MULTI,
                }

    def valid_successor(self, prompt: PromptTypes) -> bool:
        match self:
            case self.REGULAR:
                return prompt in {
                    PromptTypes.REGULAR,
                }
            case self.FORWARD:
                return prompt in {
                    PromptTypes.MULTI,
                }
            case self.BACKWARD:
                return prompt in {
                    PromptTypes.REGULAR,
                }
            case self.BIDIRECT:
                return prompt in {
                    PromptTypes.MULTI,
                }
