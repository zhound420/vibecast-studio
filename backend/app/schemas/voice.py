"""Pydantic schemas for Voice API."""

from typing import Optional

from pydantic import BaseModel, Field


class VoiceInfo(BaseModel):
    """Schema for voice information."""
    id: str = Field(..., description="Voice identifier")
    name: str = Field(..., description="Display name")
    language: str = Field(..., description="Language code")
    gender: str = Field(..., description="Gender: male/female")
    description: Optional[str] = Field(None, description="Voice description")
    has_background_music: bool = Field(False, description="Voice includes background music")
    preview_url: Optional[str] = Field(None, description="URL to preview audio")


class VoiceListResponse(BaseModel):
    """Schema for listing voices."""
    voices: list[VoiceInfo]
    total: int


# Embedded voices from VibeVoice
EMBEDDED_VOICES = [
    VoiceInfo(
        id="en-Alice_woman",
        name="Alice",
        language="en",
        gender="female",
        description="English female voice, neutral tone",
    ),
    VoiceInfo(
        id="en-Carter_man",
        name="Carter",
        language="en",
        gender="male",
        description="English male voice, professional tone",
    ),
    VoiceInfo(
        id="en-Frank_man",
        name="Frank",
        language="en",
        gender="male",
        description="English male voice, conversational",
    ),
    VoiceInfo(
        id="en-Mary_woman_bgm",
        name="Mary",
        language="en",
        gender="female",
        description="English female voice with background music",
        has_background_music=True,
    ),
    VoiceInfo(
        id="en-Maya_woman",
        name="Maya",
        language="en",
        gender="female",
        description="English female voice, warm tone",
    ),
    VoiceInfo(
        id="in-Samuel_man",
        name="Samuel",
        language="in",
        gender="male",
        description="Indian English male voice",
    ),
    VoiceInfo(
        id="zh-Anchen_man_bgm",
        name="Anchen",
        language="zh",
        gender="male",
        description="Chinese male voice with background music",
        has_background_music=True,
    ),
    VoiceInfo(
        id="zh-Bowen_man",
        name="Bowen",
        language="zh",
        gender="male",
        description="Chinese male voice",
    ),
    VoiceInfo(
        id="zh-Xinran_woman",
        name="Xinran",
        language="zh",
        gender="female",
        description="Chinese female voice",
    ),
]
