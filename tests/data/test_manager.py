from pathlib import Path

import pytest

from sachmis.data.manager import DataManager

# --- Tests for _extract_topic_from_prompt ---


@pytest.mark.parametrize(
    "prompt_input, expected_topic",
    [
        # Standard first line
        ("Hello World\nSecond line", "hello-world"),
        # Empty lines before the first real text
        ("\n\n  First Real Line  \nAnother line", "first-real-line"),
        # Special characters that slugify should handle
        ("Topic with @#$ characters!", "topic-with-characters"),
    ],
)
def test_extract_topic_from_prompt_valid(
    prompt_input: str, expected_topic: str
):
    """Test that valid multi-line strings correctly extract and slugify the first line."""
    result = DataManager._extract_topic_from_prompt(prompt_input)
    assert result == expected_topic


def test_extract_topic_from_prompt_empty():
    """Test that an empty prompt raises an AttributeError."""
    with pytest.raises(AttributeError):
        DataManager._extract_topic_from_prompt("")


def test_extract_topic_from_prompt_only_whitespace():
    """Test that a prompt containing only whitespace raises an AttributeError."""
    with pytest.raises(AttributeError):
        # A string with spaces and newlines, but no actual characters
        DataManager._extract_topic_from_prompt("   \n  \t  \n ")


# --- Tests for _match_prompt_input_and_load ---


def test_match_prompt_input_none_none(monkeypatch, tmp_path):
    """Test (None, None) fallback to default config path."""
    dummy_text = "default config text"

    # Create a temporary default file
    default_file = tmp_path / "default_prompt.txt"
    default_file.write_text(dummy_text)

    # Mock Path.cwd() to return our safe tmp_path
    monkeypatch.setattr("sachmis.data.manager.Path.cwd", lambda: tmp_path)

    # Mock the config object to point to our temp file name
    class MockConfig:
        class names:
            prompt = "default_prompt.txt"

    monkeypatch.setattr("sachmis.data.manager.config", MockConfig)

    result = DataManager._match_prompt_input_and_load(None, None)
    assert result == dummy_text


def test_match_prompt_input_path_only(tmp_path):
    """Test (Path, None) reads from the provided path."""
    dummy_text = "text from a specific path"
    custom_path = tmp_path / "custom_prompt.txt"
    custom_path.write_text(dummy_text)

    result = DataManager._match_prompt_input_and_load(
        prompt_path=custom_path, prompt_text=None
    )
    assert result == dummy_text


def test_match_prompt_input_text_only():
    """Test (None, str) uses the provided string directly."""
    dummy_text = "direct text input"
    result = DataManager._match_prompt_input_and_load(
        prompt_path=None, prompt_text=dummy_text
    )
    assert result == dummy_text


def test_match_prompt_input_both_provided():
    """Test that providing BOTH sources raises an AttributeError."""
    with pytest.raises(
        AttributeError, match="Can't load prompt from 2 sources!"
    ):
        DataManager._match_prompt_input_and_load(
            prompt_path=Path("dummy_path.txt"), prompt_text="dummy text"
        )


def test_match_prompt_input_empty_result():
    """Test that if the resolved prompt is empty, it raises an AttributeError."""
    with pytest.raises(AttributeError):
        # Directly feeding it an empty string to trigger the `if not prompt:` check
        DataManager._match_prompt_input_and_load(
            prompt_path=None, prompt_text=""
        )
