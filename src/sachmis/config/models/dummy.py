from .family import ModelFamily


class DummyFamily(ModelFamily):
    D1 = "d1"
    D2 = "d2"
    F34 = "f34"

    @property
    def unique_letter(self) -> str:
        """Unique bidirectional identifier for model company"""
        return "d"

    @property
    def target(self) -> str:
        """Identifier for FileUploader"""
        return "dummy"

    @property
    def api_name(self) -> str:
        return {
            DummyFamily.D1: "d1-pro",
            DummyFamily.D2: "d1-flash",
        }[self]
