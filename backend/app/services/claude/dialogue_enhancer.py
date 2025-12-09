"""Claude-powered dialogue enhancement service."""

from typing import List, Optional


class DialogueEnhancer:
    """
    Uses Claude API to enhance plain text into engaging dialogue.
    """

    SYSTEM_PROMPT = """You are an expert dialogue writer for audio content.
Your task is to transform input text into natural, engaging multi-speaker dialogue.

Guidelines:
- Create distinct speaker personalities
- Use natural speech patterns (contractions, filler words where appropriate)
- Break up long passages into conversational exchanges
- Add verbal acknowledgments and reactions
- Maintain the original information and meaning
- Format output as screenplay-style dialogue with speaker tags

Output format:
[Speaker 1]: Dialogue here
[Speaker 2]: Response here

Do not include any other text or explanations, only the dialogue."""

    def __init__(self, api_key: str):
        """Initialize with Claude API key."""
        self.api_key = api_key

    async def enhance_to_dialogue(
        self,
        content: str,
        style: str = "conversational",
        target_speakers: int = 2,
        speaker_names: Optional[List[str]] = None,
    ) -> str:
        """
        Transform content into multi-speaker dialogue.

        Args:
            content: Raw text content to transform
            style: Enhancement style (conversational, formal, dramatic)
            target_speakers: Number of speakers (1-4)
            speaker_names: Optional list of speaker names to use

        Returns:
            Formatted dialogue script
        """
        from anthropic import AsyncAnthropic

        if speaker_names is None:
            speaker_names = [f"Speaker {i+1}" for i in range(target_speakers)]

        # Build the user prompt
        style_guidance = {
            "conversational": "Use casual language, contractions, and natural reactions.",
            "formal": "Keep the tone professional and articulate.",
            "dramatic": "Add emotional depth and dramatic pauses where appropriate.",
        }

        user_prompt = f"""Transform the following content into a {style} dialogue
between {target_speakers} speakers ({', '.join(speaker_names)}).

{style_guidance.get(style, style_guidance['conversational'])}

Content to transform:
---
{content}
---

Generate the dialogue:"""

        # Call Claude API
        client = AsyncAnthropic(api_key=self.api_key)

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return response.content[0].text

    async def segment_with_speakers(
        self,
        content: str,
        num_speakers: int = 2,
    ) -> List[dict]:
        """
        Intelligently segment content and assign speakers using Claude.

        Returns list of {text, speaker_id, speaker_name} dicts.
        """
        from anthropic import AsyncAnthropic
        import json

        prompt = f"""Analyze this content and segment it for {num_speakers} speakers in a podcast/dialogue format.

Rules:
- Speaker 1 is the main narrator/host who explains key points
- Speaker 2 is the co-host who asks questions and provides reactions
- Each segment should be 1-3 sentences
- Maintain the flow of information
- Make it sound natural when read aloud

Return ONLY a JSON array with this exact format (no other text):
[{{"text": "segment text", "speaker_id": 1, "speaker_name": "Host"}}, ...]

Content:
---
{content}
---"""

        client = AsyncAnthropic(api_key=self.api_key)

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse JSON response
        response_text = response.content[0].text.strip()

        # Try to extract JSON if wrapped in markdown
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```json") or line.startswith("```"):
                    in_json = not in_json
                    continue
                if in_json:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)

        return json.loads(response_text)
