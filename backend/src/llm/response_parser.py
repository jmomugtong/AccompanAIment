"""Utilities for parsing LLM responses.

Extracts code blocks, parses JSON, and validates response formats
from raw text returned by language models.
"""

import json
import re
from typing import Any


class ResponseParser:
    """Static methods for extracting structured data from LLM text responses."""

    # Matches fenced code blocks: ```[optional language]\n...\n```
    _CODE_BLOCK_PATTERN = re.compile(
        r"```(?:\w+)?\s*\n(.*?)```",
        re.DOTALL,
    )

    @staticmethod
    def extract_code_blocks(response: str) -> list[str]:
        """Extract all fenced code blocks from the response.

        Handles blocks with or without a language tag (e.g. ```python or ```).

        Args:
            response: The raw LLM response text.

        Returns:
            A list of code block contents (without the fence markers).
        """
        matches = ResponseParser._CODE_BLOCK_PATTERN.findall(response)
        return [m.strip() for m in matches]

    @staticmethod
    def extract_first_code_block(response: str) -> str | None:
        """Extract the first fenced code block from the response.

        Args:
            response: The raw LLM response text.

        Returns:
            The content of the first code block, or None if no block found.
        """
        blocks = ResponseParser.extract_code_blocks(response)
        if blocks:
            return blocks[0]
        return None

    @staticmethod
    def parse_json(response: str) -> Any | None:
        """Parse JSON from the response, trying code blocks first then inline.

        Looks for JSON in fenced code blocks first. If none found, attempts
        to find and parse an inline JSON object or array.

        Args:
            response: The raw LLM response text.

        Returns:
            The parsed JSON data, or None if no valid JSON is found.
        """
        # Try extracting from code blocks first
        blocks = ResponseParser.extract_code_blocks(response)
        for block in blocks:
            try:
                return json.loads(block)
            except (json.JSONDecodeError, ValueError):
                continue

        # Try finding inline JSON (object or array)
        # Look for outermost { ... } or [ ... ]
        for pattern in [r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", r"\[.*?\]"]:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except (json.JSONDecodeError, ValueError):
                    continue

        return None

    @staticmethod
    def validate_has_code(response: str) -> bool:
        """Check whether the response contains at least one code block.

        Args:
            response: The raw LLM response text.

        Returns:
            True if the response contains a fenced code block, False otherwise.
        """
        return bool(ResponseParser._CODE_BLOCK_PATTERN.search(response))

    @staticmethod
    def validate_has_json(response: str) -> bool:
        """Check whether the response contains parseable JSON.

        Args:
            response: The raw LLM response text.

        Returns:
            True if valid JSON can be extracted, False otherwise.
        """
        return ResponseParser.parse_json(response) is not None
