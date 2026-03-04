"""Tests for LLM agent orchestration with sandboxed execution.

Covers ArrangementAgent (style reasoning, code generation, validation,
sandboxed execution, rule-based fallback), StyleAgent configs, and
prompt templates. All LLM calls are mocked.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.arrangement_agent import ArrangementAgent
from src.agents.prompts import STYLE_ANALYSIS_PROMPT, VOICING_PROMPT
from src.agents.style_agent import STYLE_CONFIGS, get_style_config


# ---------------------------------------------------------------------------
# StyleAgent tests
# ---------------------------------------------------------------------------


class TestStyleConfigs:
    """Tests for style configuration definitions."""

    def test_all_styles_present(self):
        """All five supported styles must be defined."""
        expected = {"jazz", "soulful", "rnb", "pop", "classical"}
        assert set(STYLE_CONFIGS.keys()) == expected

    @pytest.mark.parametrize("style", ["jazz", "soulful", "rnb", "pop", "classical"])
    def test_style_has_required_keys(self, style):
        """Each style config must contain extensions, voicing_type, rhythm, density."""
        config = STYLE_CONFIGS[style]
        for key in ("extensions", "voicing_type", "rhythm", "density"):
            assert key in config, f"Missing key '{key}' in {style} config"

    @pytest.mark.parametrize("style", ["jazz", "soulful", "rnb", "pop", "classical"])
    def test_extensions_is_list(self, style):
        """extensions should be a list of chord extension strings."""
        assert isinstance(STYLE_CONFIGS[style]["extensions"], list)

    @pytest.mark.parametrize("style", ["jazz", "soulful", "rnb", "pop", "classical"])
    def test_density_is_positive_number(self, style):
        """density must be a positive number."""
        density = STYLE_CONFIGS[style]["density"]
        assert isinstance(density, (int, float))
        assert density > 0

    def test_get_style_config_returns_config(self):
        """get_style_config returns the correct dict for a known style."""
        config = get_style_config("jazz")
        assert config == STYLE_CONFIGS["jazz"]

    def test_get_style_config_unknown_returns_none(self):
        """get_style_config returns None for an unknown style."""
        assert get_style_config("dubstep") is None

    def test_get_style_config_case_insensitive(self):
        """get_style_config should handle case-insensitive lookups."""
        config = get_style_config("Jazz")
        assert config == STYLE_CONFIGS["jazz"]

    def test_jazz_has_seventh_extensions(self):
        """Jazz config should include seventh chord extensions."""
        config = STYLE_CONFIGS["jazz"]
        has_seventh = any("7" in ext for ext in config["extensions"])
        assert has_seventh, "Jazz style should include seventh extensions"


# ---------------------------------------------------------------------------
# Prompt template tests
# ---------------------------------------------------------------------------


class TestPromptTemplates:
    """Tests for prompt template strings."""

    def test_voicing_prompt_is_string(self):
        assert isinstance(VOICING_PROMPT, str)

    def test_voicing_prompt_has_placeholders(self):
        """VOICING_PROMPT must contain expected format placeholders."""
        for placeholder in ("{melody}", "{chords}", "{style}", "{tempo}"):
            assert placeholder in VOICING_PROMPT, (
                f"Missing placeholder {placeholder} in VOICING_PROMPT"
            )

    def test_style_analysis_prompt_is_string(self):
        assert isinstance(STYLE_ANALYSIS_PROMPT, str)

    def test_style_analysis_prompt_has_style_placeholder(self):
        assert "{style}" in STYLE_ANALYSIS_PROMPT

    def test_voicing_prompt_mentions_music21(self):
        """The voicing prompt should instruct the LLM to generate music21 code."""
        assert "music21" in VOICING_PROMPT.lower()

    def test_voicing_prompt_format_succeeds(self):
        """Verify the prompt can be formatted without errors."""
        result = VOICING_PROMPT.format(
            melody="[60, 62, 64]",
            chords="C | F | G",
            style="jazz",
            tempo="120",
        )
        assert "jazz" in result
        assert "[60, 62, 64]" in result


# ---------------------------------------------------------------------------
# ArrangementAgent initialization tests
# ---------------------------------------------------------------------------


class TestArrangementAgentInit:
    """Tests for ArrangementAgent construction."""

    def test_init_default(self):
        """Agent initializes with default model name."""
        agent = ArrangementAgent()
        assert agent.model_name == "mistral"

    def test_init_custom_model(self):
        """Agent accepts a custom model name."""
        agent = ArrangementAgent(model_name="neural-chat")
        assert agent.model_name == "neural-chat"

    def test_init_custom_base_url(self):
        """Agent accepts a custom Ollama base URL."""
        agent = ArrangementAgent(ollama_base_url="http://remote:11434")
        assert agent.ollama_base_url == "http://remote:11434"

    def test_init_has_fallback_enabled(self):
        """Agent should have rule-based fallback enabled by default."""
        agent = ArrangementAgent()
        assert agent.fallback_enabled is True


# ---------------------------------------------------------------------------
# Style reasoning tests
# ---------------------------------------------------------------------------


class TestStyleReasoning:
    """Tests for style reasoning via the agent."""

    def test_get_style_config_from_agent(self):
        """Agent can retrieve a style configuration by name."""
        agent = ArrangementAgent()
        config = agent.get_style_config("pop")
        assert config is not None
        assert "voicing_type" in config

    def test_get_style_config_unknown_returns_none(self):
        """Agent returns None for an unknown style."""
        agent = ArrangementAgent()
        assert agent.get_style_config("metal") is None


# ---------------------------------------------------------------------------
# Code validation tests
# ---------------------------------------------------------------------------


class TestCodeValidation:
    """Tests for safety checking of generated code."""

    def setup_method(self):
        self.agent = ArrangementAgent()

    def test_safe_music21_code_passes(self):
        """Valid music21 code should pass validation."""
        safe_code = """
from music21 import stream, note, chord
s = stream.Stream()
c = chord.Chord(['C4', 'E4', 'G4'])
s.append(c)
"""
        is_valid, reason = self.agent._validate_code(safe_code)
        assert is_valid is True

    def test_exec_call_blocked(self):
        """Code containing exec() should be rejected."""
        bad_code = "exec('import os; os.system(\"rm -rf /\")')"
        is_valid, reason = self.agent._validate_code(bad_code)
        assert is_valid is False
        assert "exec" in reason.lower() or "blocked" in reason.lower()

    def test_eval_call_blocked(self):
        """Code containing eval() should be rejected."""
        bad_code = "result = eval('2 + 2')"
        is_valid, reason = self.agent._validate_code(bad_code)
        assert is_valid is False

    def test_open_call_blocked(self):
        """Code containing open() should be rejected."""
        bad_code = "f = open('/etc/passwd', 'r')"
        is_valid, reason = self.agent._validate_code(bad_code)
        assert is_valid is False

    def test_import_os_blocked(self):
        """Code importing os module should be rejected."""
        bad_code = "import os\nos.system('whoami')"
        is_valid, reason = self.agent._validate_code(bad_code)
        assert is_valid is False

    def test_import_subprocess_blocked(self):
        """Code importing subprocess should be rejected."""
        bad_code = "import subprocess\nsubprocess.run(['ls'])"
        is_valid, reason = self.agent._validate_code(bad_code)
        assert is_valid is False

    def test_dunder_import_blocked(self):
        """Code using __import__ should be rejected."""
        bad_code = "__import__('os').system('whoami')"
        is_valid, reason = self.agent._validate_code(bad_code)
        assert is_valid is False

    def test_empty_code_rejected(self):
        """Empty code string should be rejected."""
        is_valid, reason = self.agent._validate_code("")
        assert is_valid is False

    def test_music21_import_allowed(self):
        """Importing from music21 should be allowed."""
        code = "from music21 import stream, note\ns = stream.Stream()"
        is_valid, reason = self.agent._validate_code(code)
        assert is_valid is True

    def test_sys_module_blocked(self):
        """Code importing sys should be rejected."""
        bad_code = "import sys\nsys.exit(1)"
        is_valid, reason = self.agent._validate_code(bad_code)
        assert is_valid is False


# ---------------------------------------------------------------------------
# Sandboxed execution tests
# ---------------------------------------------------------------------------


class TestSandboxedExecution:
    """Tests for restricted-globals code execution."""

    def setup_method(self):
        self.agent = ArrangementAgent()

    def test_simple_expression_executes(self):
        """A simple safe expression should execute and return a result."""
        code = "result = [1, 2, 3]"
        output = self.agent._execute_sandboxed(code)
        assert output is not None
        assert output["result"] == [1, 2, 3]

    def test_dangerous_builtin_exec_blocked(self):
        """exec should not be available in the sandbox."""
        code = "exec('x = 1')"
        with pytest.raises(Exception):
            self.agent._execute_sandboxed(code)

    def test_dangerous_builtin_eval_blocked(self):
        """eval should not be available in the sandbox."""
        code = "result = eval('2 + 2')"
        with pytest.raises(Exception):
            self.agent._execute_sandboxed(code)

    def test_dangerous_builtin_open_blocked(self):
        """open should not be available in the sandbox."""
        code = "f = open('/etc/passwd')"
        with pytest.raises(Exception):
            self.agent._execute_sandboxed(code)

    def test_dangerous_builtin_import_blocked(self):
        """__import__ should not be available in the sandbox."""
        code = "os = __import__('os')"
        with pytest.raises(Exception):
            self.agent._execute_sandboxed(code)

    def test_sandbox_returns_result_variable(self):
        """The sandbox should return the value of the 'result' variable."""
        code = "x = 10\ny = 20\nresult = x + y"
        output = self.agent._execute_sandboxed(code)
        assert output["result"] == 30

    def test_sandbox_no_result_returns_empty(self):
        """If code does not set 'result', output should indicate that."""
        code = "x = 42"
        output = self.agent._execute_sandboxed(code)
        assert output.get("result") is None

    def test_sandbox_runtime_error_raises(self):
        """Runtime errors in sandboxed code should propagate."""
        code = "result = 1 / 0"
        with pytest.raises(ZeroDivisionError):
            self.agent._execute_sandboxed(code)


# ---------------------------------------------------------------------------
# Code generation tests (mocked LLM)
# ---------------------------------------------------------------------------


class TestCodeGeneration:
    """Tests for LLM-based code generation (all LLM calls mocked)."""

    def setup_method(self):
        self.agent = ArrangementAgent()
        self.melody = [60, 62, 64, 65, 67]
        self.chords = "C | F | G | C"
        self.style = "jazz"
        self.tempo = 120

    @pytest.mark.asyncio
    async def test_generate_voicing_code_returns_string(self):
        """generate_voicing_code should return a code string on success."""
        fake_code = (
            "from music21 import stream, chord\n"
            "s = stream.Stream()\n"
            "c = chord.Chord(['C4', 'E4', 'G4', 'B4'])\n"
            "s.append(c)\n"
            "result = s\n"
        )
        with patch.object(
            self.agent, "_call_llm", new_callable=AsyncMock, return_value=fake_code
        ):
            code = await self.agent.generate_voicing_code(
                self.melody, self.chords, self.style, self.tempo
            )
        assert isinstance(code, str)
        assert "stream" in code

    @pytest.mark.asyncio
    async def test_generate_voicing_code_validates_output(self):
        """Generated code should be validated before returning."""
        dangerous_code = "import os\nos.system('rm -rf /')"
        safe_fallback = "result = 'fallback'"

        with patch.object(
            self.agent, "_call_llm", new_callable=AsyncMock, return_value=dangerous_code
        ), patch.object(
            self.agent,
            "_rule_based_fallback",
            return_value=safe_fallback,
        ):
            code = await self.agent.generate_voicing_code(
                self.melody, self.chords, self.style, self.tempo
            )
        # Should have fallen back since the LLM returned unsafe code
        assert "os.system" not in code

    @pytest.mark.asyncio
    async def test_generate_voicing_code_retries_on_invalid(self):
        """Agent should fall back to rule-based on invalid code."""
        invalid_code = ""
        fallback_code = (
            "from music21 import stream, note\n"
            "s = stream.Stream()\n"
            "result = s\n"
        )

        with patch.object(
            self.agent, "_call_llm", new_callable=AsyncMock, return_value=invalid_code
        ), patch.object(
            self.agent,
            "_rule_based_fallback",
            return_value=fallback_code,
        ) as mock_fallback:
            code = await self.agent.generate_voicing_code(
                self.melody, self.chords, self.style, self.tempo
            )
        mock_fallback.assert_called_once()
        assert "stream" in code


# ---------------------------------------------------------------------------
# Fallback to rule-based templates tests
# ---------------------------------------------------------------------------


class TestRuleBasedFallback:
    """Tests for the rule-based fallback when LLM generation fails."""

    def setup_method(self):
        self.agent = ArrangementAgent()

    def test_fallback_returns_code_string(self):
        """The fallback should return a valid code string."""
        code = self.agent._rule_based_fallback(
            melody=[60, 62, 64],
            chords="C | F | G",
            style="pop",
            tempo=120,
        )
        assert isinstance(code, str)
        assert len(code) > 0

    def test_fallback_code_passes_validation(self):
        """Fallback-generated code should pass the safety validator."""
        code = self.agent._rule_based_fallback(
            melody=[60, 62, 64],
            chords="C | F | G",
            style="pop",
            tempo=120,
        )
        is_valid, reason = self.agent._validate_code(code)
        assert is_valid is True, f"Fallback code failed validation: {reason}"

    def test_fallback_code_executes_in_sandbox(self):
        """Fallback-generated code should execute in the sandbox without error."""
        code = self.agent._rule_based_fallback(
            melody=[60, 62, 64],
            chords="C | F | G",
            style="pop",
            tempo=120,
        )
        output = self.agent._execute_sandboxed(code)
        assert output is not None

    @pytest.mark.asyncio
    async def test_llm_exception_triggers_fallback(self):
        """If the LLM call raises an exception, fallback should be used."""
        with patch.object(
            self.agent,
            "_call_llm",
            new_callable=AsyncMock,
            side_effect=Exception("LLM unavailable"),
        ):
            code = await self.agent.generate_voicing_code(
                melody=[60, 62, 64],
                chords="C | F | G",
                style="pop",
                tempo=120,
            )
        assert isinstance(code, str)
        assert len(code) > 0

    @pytest.mark.asyncio
    async def test_fallback_disabled_raises_on_failure(self):
        """If fallback is disabled and LLM fails, an error should be raised."""
        agent = ArrangementAgent(fallback_enabled=False)
        with patch.object(
            agent,
            "_call_llm",
            new_callable=AsyncMock,
            side_effect=Exception("LLM unavailable"),
        ):
            with pytest.raises(Exception, match="LLM unavailable"):
                await agent.generate_voicing_code(
                    melody=[60, 62, 64],
                    chords="C | F | G",
                    style="pop",
                    tempo=120,
                )


# ---------------------------------------------------------------------------
# Response format validation tests
# ---------------------------------------------------------------------------


class TestResponseFormatValidation:
    """Tests for validating LLM response format."""

    def setup_method(self):
        self.agent = ArrangementAgent()

    def test_extract_code_from_markdown_block(self):
        """Agent should extract code from markdown code fences."""
        response = (
            "Here is the code:\n"
            "```python\n"
            "from music21 import stream\n"
            "s = stream.Stream()\n"
            "result = s\n"
            "```\n"
        )
        code = self.agent._extract_code(response)
        assert "stream" in code
        assert "```" not in code

    def test_extract_code_plain_text(self):
        """If no code fences, the entire response is treated as code."""
        response = "from music21 import stream\ns = stream.Stream()\nresult = s"
        code = self.agent._extract_code(response)
        assert "stream" in code

    def test_extract_code_empty_response(self):
        """Empty response should return empty string."""
        code = self.agent._extract_code("")
        assert code == ""

    def test_extract_code_multiple_blocks_takes_first(self):
        """If multiple code blocks exist, extract the first one."""
        response = (
            "```python\nfirst_block = True\n```\n"
            "```python\nsecond_block = True\n```\n"
        )
        code = self.agent._extract_code(response)
        assert "first_block" in code
        assert "second_block" not in code
