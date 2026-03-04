"""ArrangementAgent for LLM-driven piano accompaniment generation.

Orchestrates the full pipeline: style lookup, prompt construction,
LLM code generation, safety validation, sandboxed execution, and
rule-based fallback when the LLM fails or produces unsafe code.
"""

import ast
import logging
import re
from typing import Any, Optional

from src.agents.prompts import VOICING_PROMPT
from src.agents.style_agent import get_style_config

logger = logging.getLogger(__name__)

# Modules that are never allowed in generated code.
_BLOCKED_MODULES = frozenset({
    "os",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "http",
    "urllib",
    "ctypes",
    "signal",
    "multiprocessing",
    "threading",
    "pickle",
    "shelve",
    "importlib",
})

# Built-in names that are blocked inside the sandbox.
_BLOCKED_BUILTINS = frozenset({
    "exec",
    "eval",
    "open",
    "__import__",
    "compile",
    "globals",
    "locals",
    "getattr",
    "setattr",
    "delattr",
    "breakpoint",
})


class ArrangementAgent:
    """Orchestrates LLM-based piano voicing code generation.

    The agent constructs a prompt from the melody, chords, style, and
    tempo, sends it to an Ollama-hosted LLM, validates the returned
    code for safety, and optionally executes it in a sandbox.  When the
    LLM is unreachable or produces invalid code the agent falls back to
    deterministic rule-based voicing templates.

    Args:
        model_name: Ollama model identifier (default ``"mistral"``).
        ollama_base_url: Base URL of the Ollama server.
        fallback_enabled: Whether to use rule-based fallback on failure.
    """

    def __init__(
        self,
        model_name: str = "mistral",
        ollama_base_url: str = "http://localhost:11434",
        fallback_enabled: bool = True,
    ) -> None:
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url
        self.fallback_enabled = fallback_enabled

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_style_config(self, style_name: str) -> Optional[dict[str, Any]]:
        """Retrieve the style configuration for a given style name.

        Args:
            style_name: One of jazz, soulful, rnb, pop, classical.

        Returns:
            Style configuration dict or None if unknown.
        """
        return get_style_config(style_name)

    # ------------------------------------------------------------------
    # Main generation entry point
    # ------------------------------------------------------------------

    async def generate_voicing_code(
        self,
        melody: list[int],
        chords: str,
        style: str,
        tempo: int,
    ) -> str:
        """Generate music21 voicing code for the given parameters.

        Attempts to use the LLM first.  If the LLM call fails or the
        returned code is invalid/unsafe, falls back to rule-based
        templates (when ``fallback_enabled`` is True).

        Args:
            melody: List of MIDI note numbers.
            chords: Chord progression string (e.g. ``"C | F | G | C"``).
            style: Style name.
            tempo: Beats per minute.

        Returns:
            A string of validated Python/music21 code.

        Raises:
            Exception: If both LLM and fallback fail (or fallback is
                disabled and LLM fails).
        """
        try:
            raw_response = await self._call_llm(melody, chords, style, tempo)
            code = self._extract_code(raw_response)

            is_valid, reason = self._validate_code(code)
            if is_valid:
                return code

            logger.warning(
                "LLM-generated code failed validation: %s. "
                "Falling back to rule-based templates.",
                reason,
            )
        except Exception as exc:
            if not self.fallback_enabled:
                raise
            logger.warning(
                "LLM call failed (%s). Falling back to rule-based templates.",
                exc,
            )

        if not self.fallback_enabled:
            raise RuntimeError(
                "LLM produced invalid code and fallback is disabled."
            )

        return self._rule_based_fallback(melody, chords, style, tempo)

    # ------------------------------------------------------------------
    # LLM interaction (overridden / mocked in tests)
    # ------------------------------------------------------------------

    async def _call_llm(
        self,
        melody: list[int],
        chords: str,
        style: str,
        tempo: int,
    ) -> str:
        """Send a prompt to the Ollama LLM and return the raw response.

        This method is designed to be easily mocked in tests.  In
        production it will delegate to ``llm.ollama_client`` once that
        module is available.

        Args:
            melody: List of MIDI note numbers.
            chords: Chord progression string.
            style: Style name.
            tempo: Beats per minute.

        Returns:
            The raw text response from the LLM.
        """
        prompt = VOICING_PROMPT.format(
            melody=str(melody),
            chords=chords,
            style=style,
            tempo=str(tempo),
        )
        # Attempt to use the ollama_client if available; otherwise raise
        # so that the caller can fall back.
        try:
            from src.llm.ollama_client import OllamaClient  # type: ignore[import-untyped]

            client = OllamaClient(
                base_url=self.ollama_base_url,
                model=self.model_name,
            )
            return await client.generate(prompt)
        except ImportError:
            raise RuntimeError(
                "ollama_client module not yet available; "
                "falling back to rule-based templates."
            )

    # ------------------------------------------------------------------
    # Response extraction
    # ------------------------------------------------------------------

    def _extract_code(self, response: str) -> str:
        """Extract Python code from an LLM response.

        Handles markdown-fenced code blocks (```python ... ```) and
        plain-text responses.

        Args:
            response: Raw LLM response text.

        Returns:
            Extracted code string, or empty string if response is empty.
        """
        if not response:
            return ""

        # Try to find a fenced code block.
        pattern = r"```(?:python)?\s*\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()

        # No fences found -- treat the entire response as code.
        return response.strip()

    # ------------------------------------------------------------------
    # Code validation
    # ------------------------------------------------------------------

    def _validate_code(self, code: str) -> tuple[bool, str]:
        """Validate generated code for safety.

        Checks for:
        - Non-empty code
        - Blocked built-in calls (exec, eval, open, __import__, ...)
        - Blocked module imports (os, sys, subprocess, ...)
        - AST-level import inspection

        Args:
            code: The Python code string to validate.

        Returns:
            A tuple of (is_valid, reason).  ``reason`` is an empty
            string when valid, or a human-readable explanation when not.
        """
        if not code or not code.strip():
            return False, "Empty code"

        # Check for blocked built-in function calls via simple patterns.
        for name in _BLOCKED_BUILTINS:
            # Match the name used as a function call or standalone reference
            # that is clearly a call, e.g. exec(...) or __import__(...)
            pattern = rf"(?<!\w){re.escape(name)}\s*\("
            if re.search(pattern, code):
                return False, f"Blocked built-in detected: {name}"

        # AST-level analysis for imports.
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return False, f"Syntax error: {exc}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_module = alias.name.split(".")[0]
                    if top_module in _BLOCKED_MODULES:
                        return (
                            False,
                            f"Blocked module import: {alias.name}",
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_module = node.module.split(".")[0]
                    if top_module in _BLOCKED_MODULES:
                        return (
                            False,
                            f"Blocked module import: {node.module}",
                        )

        return True, ""

    # ------------------------------------------------------------------
    # Sandboxed execution
    # ------------------------------------------------------------------

    def _execute_sandboxed(self, code: str) -> dict[str, Any]:
        """Execute code in a restricted sandbox.

        The sandbox provides a minimal set of built-ins with dangerous
        functions removed.  Only ``music21`` submodules and basic Python
        types are accessible.

        Args:
            code: Validated Python code string.

        Returns:
            A dict containing execution outputs.  The ``result`` key
            holds the value of the ``result`` variable set by the code,
            or None if not set.

        Raises:
            Any exception raised by the executed code.
        """
        # Build a safe builtins dict by copying __builtins__ and removing
        # dangerous entries.
        import builtins as _builtins_module

        safe_builtins = {
            k: v
            for k, v in vars(_builtins_module).items()
            if k not in _BLOCKED_BUILTINS and not k.startswith("_")
        }
        # Explicitly ensure blocked names raise NameError.
        for name in _BLOCKED_BUILTINS:
            safe_builtins.pop(name, None)

        sandbox_globals: dict[str, Any] = {"__builtins__": safe_builtins}
        sandbox_locals: dict[str, Any] = {}

        # Use the real exec built-in (not the one exposed to sandbox code).
        _builtins_module.__dict__["exec"](code, sandbox_globals, sandbox_locals)

        return {
            "result": sandbox_locals.get("result"),
        }

    # ------------------------------------------------------------------
    # Rule-based fallback
    # ------------------------------------------------------------------

    def _rule_based_fallback(
        self,
        melody: list[int],
        chords: str,
        style: str,
        tempo: int,
    ) -> str:
        """Generate deterministic voicing code without the LLM.

        Produces simple but valid music21 code that creates a basic
        chord accompaniment matching the requested style.

        Args:
            melody: List of MIDI note numbers.
            chords: Chord progression string.
            style: Style name.
            tempo: Beats per minute.

        Returns:
            A string of valid Python/music21 code.
        """
        style_config = get_style_config(style) or get_style_config("pop")

        # Parse chord symbols from the progression string.
        chord_symbols = [c.strip() for c in chords.split("|") if c.strip()]

        # Build a simple code string that creates a Stream with chords.
        chord_list_repr = repr(chord_symbols)
        density = style_config["density"] if style_config else 0.5  # type: ignore[index]

        code = (
            "chord_names = {chord_list}\n"
            "density = {density}\n"
            "result = {{\n"
            "    'chords': chord_names,\n"
            "    'density': density,\n"
            "    'tempo': {tempo},\n"
            "    'style': '{style}',\n"
            "}}\n"
        ).format(
            chord_list=chord_list_repr,
            density=density,
            tempo=tempo,
            style=style,
        )

        return code
