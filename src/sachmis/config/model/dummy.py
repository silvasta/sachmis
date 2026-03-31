from .family import ModelFamily


class DummyFamily(ModelFamily):
    D1 = "d1"
    D2 = "d2"

    @property
    def category_unique(self) -> str:
        """Used for pydantic, Models -> str -> Models and for CLI"""
        return "d"

    @property
    def api_name(self) -> str:
        return {
            self.D1: "d1-pro",
            self.D2: "d1-flash",
        }[self]
