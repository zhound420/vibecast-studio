"""Script parser for converting text to segments."""

import re
from typing import List, Dict, Optional


class ScriptParser:
    """
    Parser for converting various script formats into segments.

    Supported formats:
    - bracket: [1] Text or [Speaker Name] Text
    - colon: Speaker Name: Text
    - numbered: 1. Text or 1) Text
    - auto: Attempts to detect format automatically
    """

    # Patterns for different formats
    BRACKET_PATTERN = re.compile(
        r"^\[(\d+|[^\]]+)\]\s*(.+)$",
        re.MULTILINE
    )
    COLON_PATTERN = re.compile(
        r"^([A-Za-z][A-Za-z0-9\s]{0,30}):\s*(.+)$",
        re.MULTILINE
    )
    NUMBERED_PATTERN = re.compile(
        r"^(\d+)[.)]\s*(.+)$",
        re.MULTILINE
    )
    DIRECTION_PATTERN = re.compile(
        r"\[([^\]]+)\]",
    )

    def parse(
        self,
        text: str,
        format: str = "auto",
    ) -> List[Dict]:
        """
        Parse text into a list of segments.

        Args:
            text: The script text to parse
            format: Format to use (auto, bracket, colon, numbered, plain)

        Returns:
            List of segment dictionaries with keys:
            - text: The segment text
            - speaker_id: Numeric speaker ID (1-4)
            - speaker_name: Optional speaker name
            - direction: Optional acting direction
        """
        if format == "auto":
            format = self._detect_format(text)

        if format == "bracket":
            return self._parse_bracket(text)
        elif format == "colon":
            return self._parse_colon(text)
        elif format == "numbered":
            return self._parse_numbered(text)
        else:
            return self._parse_plain(text)

    def _detect_format(self, text: str) -> str:
        """Detect the most likely format of the script."""
        lines = text.strip().split("\n")
        sample_lines = [l.strip() for l in lines[:20] if l.strip()]

        bracket_matches = sum(
            1 for l in sample_lines if self.BRACKET_PATTERN.match(l)
        )
        colon_matches = sum(
            1 for l in sample_lines if self.COLON_PATTERN.match(l)
        )
        numbered_matches = sum(
            1 for l in sample_lines if self.NUMBERED_PATTERN.match(l)
        )

        if bracket_matches >= len(sample_lines) * 0.5:
            return "bracket"
        elif colon_matches >= len(sample_lines) * 0.5:
            return "colon"
        elif numbered_matches >= len(sample_lines) * 0.5:
            return "numbered"
        else:
            return "plain"

    def _parse_bracket(self, text: str) -> List[Dict]:
        """Parse bracket format: [1] Text or [Speaker Name] Text"""
        segments = []
        speaker_map = {}  # name -> id

        for match in self.BRACKET_PATTERN.finditer(text):
            speaker_ref = match.group(1)
            segment_text = match.group(2).strip()

            # Extract any direction tags
            direction = None
            dir_match = self.DIRECTION_PATTERN.search(segment_text)
            if dir_match:
                direction = dir_match.group(1)
                segment_text = self.DIRECTION_PATTERN.sub("", segment_text).strip()

            # Determine speaker ID
            if speaker_ref.isdigit():
                speaker_id = min(int(speaker_ref), 4)
                speaker_name = None
            else:
                speaker_name = speaker_ref
                if speaker_name not in speaker_map:
                    speaker_map[speaker_name] = len(speaker_map) + 1
                speaker_id = min(speaker_map[speaker_name], 4)

            segments.append({
                "text": segment_text,
                "speaker_id": speaker_id,
                "speaker_name": speaker_name,
                "direction": direction,
            })

        return segments

    def _parse_colon(self, text: str) -> List[Dict]:
        """Parse colon format: Speaker Name: Text"""
        segments = []
        speaker_map = {}

        for match in self.COLON_PATTERN.finditer(text):
            speaker_name = match.group(1).strip()
            segment_text = match.group(2).strip()

            # Extract any direction tags
            direction = None
            dir_match = self.DIRECTION_PATTERN.search(segment_text)
            if dir_match:
                direction = dir_match.group(1)
                segment_text = self.DIRECTION_PATTERN.sub("", segment_text).strip()

            # Map speaker to ID
            if speaker_name not in speaker_map:
                speaker_map[speaker_name] = len(speaker_map) + 1
            speaker_id = min(speaker_map[speaker_name], 4)

            segments.append({
                "text": segment_text,
                "speaker_id": speaker_id,
                "speaker_name": speaker_name,
                "direction": direction,
            })

        return segments

    def _parse_numbered(self, text: str) -> List[Dict]:
        """Parse numbered format: 1. Text"""
        segments = []

        for match in self.NUMBERED_PATTERN.finditer(text):
            speaker_id = min(int(match.group(1)), 4)
            segment_text = match.group(2).strip()

            direction = None
            dir_match = self.DIRECTION_PATTERN.search(segment_text)
            if dir_match:
                direction = dir_match.group(1)
                segment_text = self.DIRECTION_PATTERN.sub("", segment_text).strip()

            segments.append({
                "text": segment_text,
                "speaker_id": speaker_id,
                "speaker_name": None,
                "direction": direction,
            })

        return segments

    def _parse_plain(self, text: str) -> List[Dict]:
        """Parse plain text by splitting into paragraphs."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        segments = []
        for i, para in enumerate(paragraphs):
            # Alternate between speakers for plain text
            speaker_id = (i % 2) + 1

            segments.append({
                "text": para,
                "speaker_id": speaker_id,
                "speaker_name": None,
                "direction": None,
            })

        return segments
