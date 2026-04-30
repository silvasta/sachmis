from .family import ModelFamily

# IMPORTANT: Last update: 18.03.2026


class Geminis(ModelFamily):
    G3 = "g3"
    G31F = "g31f"
    G3F = "g3f"
    G3I = "g3i"
    GE2 = "ge2"

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
            Geminis.G31F: "gemini-3.1-flash-lite-preview",
            Geminis.G3: "gemini-3.1-pro-preview",
            Geminis.G3F: "gemini-3-flash-preview",
            Geminis.G3I: "gemini-3-pro-image-preview",
            Geminis.GE2: "gemini-embedding-2-preview",
        }[self]
