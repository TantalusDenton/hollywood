import pytest
from pydantic import ValidationError

from app.models.schemas import Character, GenerationSettings, StoryAnalysis


def test_generation_settings_reject_unknown_provider_configuration():
    with pytest.raises(ValidationError):
        GenerationSettings.model_validate({"not_a_setting": True})


def test_character_requires_canonical_visual_fields():
    with pytest.raises(ValidationError):
        Character.model_validate({"name": "Missing fields"})
