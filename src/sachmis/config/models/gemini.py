from .family import ModelFamily


class Geminis(ModelFamily):
    G31 = "g3"
    G31F = "g31f"
    G3I = "g3i"
    GR = "gr"

    # NOTE: Ideas
    # https://ai.google.dev/gemini-api/docs/robotics-overview

    # TODO: price list
    @property
    def unique_letter(self) -> str:
        """Used for pydantic, Models -> str -> Models and for CLI"""
        return "g"

    @property
    def api_name(self) -> str:
        return {
            Geminis.G31: "gemini-3.1-pro-preview",
            Geminis.G31F: "gemini-3.1-flash-lite-preview",
            Geminis.G3I: "gemini-3-pro-image-preview",
            Geminis.GR: "gemini-robotics-er-1.6-preview",
        }[self]

    @property
    def target(self) -> str:
        """Identifier for FileUploader"""
        return "google"
