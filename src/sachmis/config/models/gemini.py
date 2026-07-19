from sstcore.utils.color import ColorBox

from .family import ModelFamily

c = ColorBox()


class Geminis(ModelFamily):
    G31 = "g3"
    G3I = "g3i"
    GR = "gr"
    G35F = "g35f"

    # NOTE: Ideas
    # https://ai.google.dev/gemini-api/docs/robotics-overview

    # TODO: usage calculation
    @property
    def unique_letter(self) -> str:
        """Used for pydantic, Models -> str -> Models and for CLI"""
        return "g"

    @property
    def family(self) -> str:
        """Full name that is used for API call"""
        return c.green(self.__class__.__name__)

    @property
    def api_name(self) -> str:
        return {
            Geminis.G31: "gemini-3.1-pro-preview",
            Geminis.G3I: "gemini-3-pro-image-preview",
            Geminis.GR: "gemini-robotics-er-1.6-preview",
            Geminis.G35F: "gemini-3.5-flash",
        }[self]

    @property
    def target(self) -> str:
        """Identifier for FileUploader"""
        return "google"
