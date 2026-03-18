from pathlib import Path

from sachmis.config.manager import config

from .arboreal import Biome, Forest, Sprout, Tree

# class AppSettings(BaseModel):
#     # TODO: forest tree for local,global
#     theme: str = "dark"
#     volume: int = 80
#
#
# class UserProfile(BaseModel):
#     # TODO: forest tree for local,global
#     username: str = "guest"
#     level: int = 1


# NEXT: bring in the new arboreal


class DataManager:
    """Loads Pydantic models on entry, saves them on clean exit."""

    def __init__(
        self,  # TODO: proper args
    ):

        self.settings_file = self.config_dir / "settings.json"
        self.profile_file = self.config_dir / "profile.json"

        # Placeholders for the Pydantic instances
        self.settings: AppSettings | None = None
        self.profile: UserProfile | None = None

    def __enter__(self):
        """Triggered automatically by 'with'. Loads the JSON files."""
        print("--> [DataManager] Loading JSON data...")

        # Load or create Settings
        if self.settings_file.exists():
            self.settings = AppSettings.model_validate_json(
                self.settings_file.read_text()
            )
        else:
            self.settings = AppSettings()

        # Load or create Profile
        if self.profile_file.exists():
            self.profile = UserProfile.model_validate_json(
                self.profile_file.read_text()
            )
        else:
            self.profile = UserProfile()

        # Yields this class instance to the 'as data' variable
        return self

    def __exit__(
        self,
        exception_type,  # LATER: decide how to handle which error
        exception_value,
        exception_trace_back,
    ):
        """Triggered automatically when leaving the 'with' block."""
        if exc_type is None:
            # If no errors happened inside the 'with' block, save to disk
            print("<-- [DataManager] Clean exit: Saving data to JSON...")
            self.settings_file.write_text(
                self.settings.model_dump_json(indent=4)
            )
            self.profile_file.write_text(
                self.profile.model_dump_json(indent=4)
            )
        else:
            # If an error happened (e.g. crash in UI), abort save
            print(
                f"<-- [DataManager] Error ({exception_type.__name__}) detected: Aborting save."
            )

        # INFO: example error handling
        if issubclass(exception_type, ValueError):
            # We catch the error, log the message (exc_val), and skip the save
            print(
                f"<-- Harmless UI Error caught: '{exception_value}'. Skipping save."
            )

            # Returning True tells Python: "I handled this, DO NOT crash the app."
            return True
        # Returning False allows any exception to propagate up to the caller
        return False
