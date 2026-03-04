"""Tests for LLM integration layer: OllamaClient, PromptTemplate, ResponseParser."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.llm.ollama_client import OllamaClient
from src.llm.prompt_templates import PromptTemplate
from src.llm.response_parser import ResponseParser


# ---------------------------------------------------------------------------
# OllamaClient tests
# ---------------------------------------------------------------------------
class TestOllamaClientInit:
    """Test OllamaClient initialization and configuration."""

    def test_default_url_and_model(self):
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434"
        assert client.model == "mistral"

    def test_custom_url_and_model(self):
        client = OllamaClient(
            base_url="http://myhost:9999",
            model="llama2",
        )
        assert client.base_url == "http://myhost:9999"
        assert client.model == "llama2"

    def test_custom_temperature(self):
        client = OllamaClient(temperature=0.3)
        assert client.temperature == 0.3

    def test_custom_timeout(self):
        client = OllamaClient(timeout=60.0)
        assert client.timeout == 60.0

    def test_default_temperature(self):
        client = OllamaClient()
        assert client.temperature == 0.7

    def test_default_timeout(self):
        client = OllamaClient()
        assert client.timeout == 120.0

    def test_trailing_slash_stripped_from_url(self):
        client = OllamaClient(base_url="http://localhost:11434/")
        assert client.base_url == "http://localhost:11434"


class TestOllamaClientHealthCheck:
    """Test OllamaClient.health_check() with mocked HTTP calls."""

    @patch("src.llm.ollama_client.httpx.get")
    def test_health_check_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = OllamaClient()
        result = client.health_check()

        assert result is True
        mock_get.assert_called_once_with(
            "http://localhost:11434/api/tags",
            timeout=10.0,
        )

    @patch("src.llm.ollama_client.httpx.get")
    def test_health_check_server_down(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        client = OllamaClient()
        result = client.health_check()

        assert result is False

    @patch("src.llm.ollama_client.httpx.get")
    def test_health_check_timeout(self, mock_get):
        mock_get.side_effect = httpx.TimeoutException("timed out")

        client = OllamaClient()
        result = client.health_check()

        assert result is False

    @patch("src.llm.ollama_client.httpx.get")
    def test_health_check_non_200(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        client = OllamaClient()
        result = client.health_check()

        assert result is False


class TestOllamaClientGenerate:
    """Test OllamaClient.generate() with mocked HTTP calls."""

    @patch("src.llm.ollama_client.httpx.post")
    def test_generate_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "mistral",
            "response": "Here is a C major chord voicing.",
            "done": True,
        }
        mock_post.return_value = mock_response

        client = OllamaClient()
        result = client.generate("Write a C major chord voicing")

        assert result == "Here is a C major chord voicing."
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[0][0] == "http://localhost:11434/api/generate"
        payload = call_kwargs[1]["json"]
        assert payload["model"] == "mistral"
        assert payload["prompt"] == "Write a C major chord voicing"
        assert payload["stream"] is False

    @patch("src.llm.ollama_client.httpx.post")
    def test_generate_with_custom_temperature(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "mistral",
            "response": "result",
            "done": True,
        }
        mock_post.return_value = mock_response

        client = OllamaClient(temperature=0.2)
        client.generate("test prompt")

        payload = mock_post.call_args[1]["json"]
        assert payload["options"]["temperature"] == 0.2

    @patch("src.llm.ollama_client.httpx.post")
    def test_generate_timeout_raises(self, mock_post):
        mock_post.side_effect = httpx.TimeoutException("Request timed out")

        client = OllamaClient(timeout=5.0)
        with pytest.raises(TimeoutError, match="timed out"):
            client.generate("slow prompt")

    @patch("src.llm.ollama_client.httpx.post")
    def test_generate_model_not_found(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "model 'nonexistent' not found"
        mock_post.return_value = mock_response

        client = OllamaClient(model="nonexistent")
        with pytest.raises(ValueError, match="not found"):
            client.generate("test")

    @patch("src.llm.ollama_client.httpx.post")
    def test_generate_server_error_raises(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        client = OllamaClient()
        with pytest.raises(RuntimeError, match="Ollama server error"):
            client.generate("test")

    @patch("src.llm.ollama_client.httpx.post")
    def test_generate_uses_configured_timeout(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "ok",
            "done": True,
        }
        mock_post.return_value = mock_response

        client = OllamaClient(timeout=42.0)
        client.generate("prompt")

        assert mock_post.call_args[1]["timeout"] == 42.0


class TestOllamaClientRetry:
    """Test retry logic with exponential backoff on transient failures."""

    @patch("src.llm.ollama_client.time.sleep")
    @patch("src.llm.ollama_client.httpx.post")
    def test_retry_on_connection_error_then_success(self, mock_post, mock_sleep):
        """First two calls fail with connection error, third succeeds."""
        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.json.return_value = {
            "response": "recovered",
            "done": True,
        }
        mock_post.side_effect = [
            httpx.ConnectError("refused"),
            httpx.ConnectError("refused"),
            mock_success,
        ]

        client = OllamaClient(max_retries=3)
        result = client.generate("retry me")

        assert result == "recovered"
        assert mock_post.call_count == 3
        # Exponential backoff: sleep(1), sleep(2)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @patch("src.llm.ollama_client.time.sleep")
    @patch("src.llm.ollama_client.httpx.post")
    def test_retry_exhausted_raises(self, mock_post, mock_sleep):
        """All retry attempts fail -- should raise ConnectionError."""
        mock_post.side_effect = httpx.ConnectError("down")

        client = OllamaClient(max_retries=3)
        with pytest.raises(ConnectionError, match="Failed to connect"):
            client.generate("doomed prompt")

        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("src.llm.ollama_client.time.sleep")
    @patch("src.llm.ollama_client.httpx.post")
    def test_no_retry_on_non_transient_error(self, mock_post, mock_sleep):
        """Model-not-found (404) should NOT be retried."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "model 'bad' not found"
        mock_post.return_value = mock_response

        client = OllamaClient(model="bad", max_retries=3)
        with pytest.raises(ValueError, match="not found"):
            client.generate("test")

        assert mock_post.call_count == 1
        mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# PromptTemplate tests
# ---------------------------------------------------------------------------
class TestPromptTemplate:
    """Test PromptTemplate rendering with variable substitution."""

    def test_render_basic_substitution(self):
        template = PromptTemplate("Hello, {name}!")
        result = template.render(name="World")
        assert result == "Hello, World!"

    def test_render_multiple_variables(self):
        template = PromptTemplate(
            "Generate a {style} voicing for {chord} in {key} major."
        )
        result = template.render(style="jazz", chord="Cmaj7", key="C")
        assert result == "Generate a jazz voicing for Cmaj7 in C major."

    def test_render_missing_variable_raises(self):
        template = PromptTemplate("Hello, {name}! Your style is {style}.")
        with pytest.raises(KeyError):
            template.render(name="Alice")

    def test_render_preserves_literal_text(self):
        template = PromptTemplate("No variables here.")
        result = template.render()
        assert result == "No variables here."

    def test_render_multiline_template(self):
        template = PromptTemplate(
            "Chord: {chord}\nStyle: {style}\nTempo: {tempo}"
        )
        result = template.render(chord="Am7", style="soulful", tempo="120")
        assert result == "Chord: Am7\nStyle: soulful\nTempo: 120"

    def test_template_text_stored(self):
        text = "Generate {style} piano accompaniment."
        template = PromptTemplate(text)
        assert template.template == text


class TestBuiltinPromptTemplates:
    """Test the built-in prompt templates for voicing and style analysis."""

    def test_voicing_generation_template_renders(self):
        from src.llm.prompt_templates import VOICING_GENERATION_TEMPLATE

        result = VOICING_GENERATION_TEMPLATE.render(
            chord_progression="C | Am | F | G",
            style="jazz",
            tempo="120",
            time_signature="4/4",
            melody_notes="C4 E4 G4 A4",
        )
        assert "C | Am | F | G" in result
        assert "jazz" in result
        assert "120" in result
        assert "4/4" in result
        assert "C4 E4 G4 A4" in result

    def test_style_analysis_template_renders(self):
        from src.llm.prompt_templates import STYLE_ANALYSIS_TEMPLATE

        result = STYLE_ANALYSIS_TEMPLATE.render(
            style="soulful",
            description="Warm and emotional piano with gospel influences.",
        )
        assert "soulful" in result
        assert "Warm and emotional" in result


# ---------------------------------------------------------------------------
# ResponseParser tests
# ---------------------------------------------------------------------------
class TestResponseParserCodeExtraction:
    """Test extraction of code blocks from LLM responses."""

    def test_extract_python_code_block(self):
        response = (
            "Here is the voicing code:\n"
            "```python\n"
            "from music21 import chord\n"
            "c = chord.Chord(['C4', 'E4', 'G4'])\n"
            "```\n"
            "This creates a C major chord."
        )
        blocks = ResponseParser.extract_code_blocks(response)
        assert len(blocks) == 1
        assert "from music21 import chord" in blocks[0]
        assert "chord.Chord" in blocks[0]

    def test_extract_multiple_code_blocks(self):
        response = (
            "First block:\n"
            "```python\nprint('hello')\n```\n"
            "Second block:\n"
            "```python\nprint('world')\n```\n"
        )
        blocks = ResponseParser.extract_code_blocks(response)
        assert len(blocks) == 2
        assert "hello" in blocks[0]
        assert "world" in blocks[1]

    def test_extract_code_block_without_language_tag(self):
        response = "Code:\n```\nx = 42\n```\nDone."
        blocks = ResponseParser.extract_code_blocks(response)
        assert len(blocks) == 1
        assert "x = 42" in blocks[0]

    def test_no_code_blocks_returns_empty_list(self):
        response = "There is no code here, just plain text."
        blocks = ResponseParser.extract_code_blocks(response)
        assert blocks == []

    def test_extract_first_code_block(self):
        response = (
            "```python\nfirst()\n```\n"
            "```python\nsecond()\n```\n"
        )
        block = ResponseParser.extract_first_code_block(response)
        assert block is not None
        assert "first()" in block

    def test_extract_first_code_block_returns_none_when_empty(self):
        response = "No code."
        block = ResponseParser.extract_first_code_block(response)
        assert block is None


class TestResponseParserJSON:
    """Test JSON parsing from LLM responses."""

    def test_parse_json_from_code_block(self):
        response = (
            "Here is the analysis:\n"
            '```json\n{"style": "jazz", "tempo": 120}\n```'
        )
        data = ResponseParser.parse_json(response)
        assert data == {"style": "jazz", "tempo": 120}

    def test_parse_json_inline(self):
        response = 'The result is {"key": "C", "mode": "major"} as shown.'
        data = ResponseParser.parse_json(response)
        assert data == {"key": "C", "mode": "major"}

    def test_parse_json_no_json_returns_none(self):
        response = "This response has no JSON at all."
        data = ResponseParser.parse_json(response)
        assert data is None

    def test_parse_json_array(self):
        response = '```json\n["C", "Am", "F", "G"]\n```'
        data = ResponseParser.parse_json(response)
        assert data == ["C", "Am", "F", "G"]

    def test_parse_json_malformed_returns_none(self):
        response = '{"broken": json, not valid}'
        data = ResponseParser.parse_json(response)
        assert data is None


class TestResponseParserValidation:
    """Test response format validation."""

    def test_validate_has_code_true(self):
        response = "```python\nprint('hi')\n```"
        assert ResponseParser.validate_has_code(response) is True

    def test_validate_has_code_false(self):
        response = "Just a text response."
        assert ResponseParser.validate_has_code(response) is False

    def test_validate_has_json_true(self):
        response = '{"key": "value"}'
        assert ResponseParser.validate_has_json(response) is True

    def test_validate_has_json_false(self):
        response = "No JSON content here."
        assert ResponseParser.validate_has_json(response) is False
