"""Prompt templates for the LLM agent system.

These templates are used by the ArrangementAgent to instruct the LLM
to generate music21-based piano voicing code.
"""

VOICING_PROMPT = """\
You are an expert music arranger specializing in piano accompaniment.
Given the following inputs, generate Python code using the music21 library
that creates a piano accompaniment part.

Melody (MIDI note numbers): {melody}
Chord progression: {chords}
Style: {style}
Tempo (BPM): {tempo}

Requirements:
- Use music21 stream, note, chord, and duration modules.
- Create a music21 Stream object and assign it to a variable called `result`.
- Voice the chords appropriately for the given style.
- Ensure rhythmic patterns match the style conventions.
- Do NOT import any modules other than music21 submodules.
- Do NOT use exec, eval, open, os, sys, subprocess, or __import__.

Return ONLY valid Python code, no explanations.
"""

STYLE_ANALYSIS_PROMPT = """\
Analyze the musical style "{style}" and describe:
1. Typical chord extensions used (e.g., 7ths, 9ths, 13ths)
2. Common voicing techniques (close, open, drop-2, shell, etc.)
3. Rhythmic patterns and density
4. Typical register and hand positioning
5. Characteristic harmonic movements

Provide a structured analysis that can guide piano accompaniment generation.
"""
