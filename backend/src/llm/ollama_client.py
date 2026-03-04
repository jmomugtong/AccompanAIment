"""Synchronous HTTP client for the Ollama LLM server.

Provides health checking, text generation with configurable model/temperature,
and retry logic with exponential backoff for transient failures.
"""

import time
from typing import Any

import httpx


class OllamaClient:
    """Client for interacting with an Ollama server over HTTP.

    Args:
        base_url: Base URL of the Ollama server (default: http://localhost:11434).
        model: Model name to use for generation (default: mistral).
        temperature: Sampling temperature (default: 0.7).
        timeout: Request timeout in seconds (default: 120.0).
        max_retries: Maximum number of attempts for transient failures (default: 3).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "mistral",
        temperature: float = 0.7,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

    def health_check(self) -> bool:
        """Check if the Ollama server is reachable and responding.

        Returns:
            True if the server responds with HTTP 200, False otherwise.
        """
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags",
                timeout=10.0,
            )
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    def generate(self, prompt: str) -> str:
        """Send a text generation request to the Ollama server.

        Uses retry logic with exponential backoff for transient connection
        errors. Non-transient errors (e.g. model not found) are raised
        immediately without retrying.

        Args:
            prompt: The text prompt to send to the model.

        Returns:
            The generated text response from the model.

        Raises:
            TimeoutError: If the request times out after all retries.
            ValueError: If the specified model is not found (HTTP 404).
            RuntimeError: If the server returns a non-success status code.
            ConnectionError: If all retry attempts fail due to connection issues.
        """
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                return self._do_generate(prompt)
            except httpx.ConnectError as exc:
                last_exception = exc
                if attempt < self.max_retries - 1:
                    backoff = 2**attempt
                    time.sleep(backoff)
            except httpx.TimeoutException:
                raise TimeoutError(
                    f"Ollama request timed out after {self.timeout}s"
                )

        raise ConnectionError(
            f"Failed to connect to Ollama at {self.base_url} "
            f"after {self.max_retries} attempts: {last_exception}"
        )

    def _do_generate(self, prompt: str) -> str:
        """Execute a single generation request (no retries).

        Args:
            prompt: The text prompt.

        Returns:
            The model response text.

        Raises:
            ValueError: If the model is not found.
            RuntimeError: On server errors.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code == 404:
            raise ValueError(
                f"Model '{self.model}' not found on Ollama server: "
                f"{response.text}"
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"Ollama server error (HTTP {response.status_code}): "
                f"{response.text}"
            )

        data = response.json()
        return data["response"]
