"""Prompt templates for LLM interactions.

Provides a simple PromptTemplate class for variable substitution and
pre-built templates for piano accompaniment voicing generation and
style analysis.
"""


class PromptTemplate:
    """A simple prompt template with named variable substitution.

    Uses Python str.format() syntax ({variable_name}) for placeholders.

    Args:
        template: The template string with {variable} placeholders.
    """

    def __init__(self, template: str) -> None:
        self.template = template

    def render(self, **kwargs: str) -> str:
        """Render the template by substituting variables.

        Args:
            **kwargs: Variable name-value pairs to substitute into the template.

        Returns:
            The rendered string with all variables replaced.

        Raises:
            KeyError: If a required template variable is not provided.
        """
        return self.template.format(**kwargs)


# ---------------------------------------------------------------------------
# Built-in prompt templates
# ---------------------------------------------------------------------------

VOICING_GENERATION_TEMPLATE = PromptTemplate(
    "You are an expert piano accompanist. Generate music21 Python code that "
    "creates a piano accompaniment for the following parameters.\n"
    "\n"
    "Chord progression: {chord_progression}\n"
    "Style: {style}\n"
    "Tempo: {tempo} BPM\n"
    "Time signature: {time_signature}\n"
    "Melody notes: {melody_notes}\n"
    "\n"
    "Requirements:\n"
    "- Use music21 library to create the accompaniment\n"
    "- Ensure voicings are idiomatic for the specified style\n"
    "- Avoid doubling melody notes in the accompaniment\n"
    "- Return the code inside a ```python code block\n"
    "- The code should produce a music21 Score object named 'score'"
)

STYLE_ANALYSIS_TEMPLATE = PromptTemplate(
    "Analyze the following piano accompaniment style and describe its "
    "key characteristics for generating idiomatic voicings.\n"
    "\n"
    "Style: {style}\n"
    "Description: {description}\n"
    "\n"
    "Provide your analysis as JSON with the following keys:\n"
    "- voicing_type: (e.g., shell, rootless, block, broken)\n"
    "- rhythm_pattern: (e.g., whole notes, comping, arpeggiated)\n"
    "- register: (e.g., middle, low, wide)\n"
    "- dynamics: (e.g., soft, moderate, varied)\n"
    "- extensions: list of common chord extensions used\n"
    "\n"
    "Return the JSON inside a ```json code block."
)
