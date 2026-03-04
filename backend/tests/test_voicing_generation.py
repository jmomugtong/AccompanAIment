"""Tests for chord voicing generation: triads, inversions, voice leading, style voicings."""

import pytest

from src.music.voicing_generator import VoicingGenerator


class TestBasicTriadVoicing:
    """Test basic triad voicing in root position."""

    def test_c_major_triad(self):
        """C major triad should contain C, E, G (MIDI 48, 52, 55 or equivalent)."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C")
        # Should have at least 3 notes
        assert len(voicing) >= 3
        # All should be integers (MIDI note numbers)
        assert all(isinstance(n, int) for n in voicing)
        # Check pitch classes: C=0, E=4, G=7
        pitch_classes = sorted(set(n % 12 for n in voicing))
        assert 0 in pitch_classes  # C
        assert 4 in pitch_classes  # E
        assert 7 in pitch_classes  # G

    def test_a_minor_triad(self):
        """Am triad should contain A, C, E."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("Am")
        pitch_classes = sorted(set(n % 12 for n in voicing))
        assert 9 in pitch_classes  # A
        assert 0 in pitch_classes  # C
        assert 4 in pitch_classes  # E

    def test_g_major_triad(self):
        """G major triad should contain G, B, D."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("G")
        pitch_classes = sorted(set(n % 12 for n in voicing))
        assert 7 in pitch_classes  # G
        assert 11 in pitch_classes  # B
        assert 2 in pitch_classes  # D

    def test_f_major_triad(self):
        """F major triad should contain F, A, C."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("F")
        pitch_classes = sorted(set(n % 12 for n in voicing))
        assert 5 in pitch_classes  # F
        assert 9 in pitch_classes  # A
        assert 0 in pitch_classes  # C

    def test_voicing_returns_list_of_ints(self):
        """Voicing must return a list of MIDI note numbers (integers)."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C")
        assert isinstance(voicing, list)
        assert all(isinstance(n, int) for n in voicing)

    def test_voicing_is_sorted_ascending(self):
        """Voicing notes should be sorted from lowest to highest."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C")
        assert voicing == sorted(voicing)

    def test_d_minor_triad(self):
        """Dm triad should contain D, F, A."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("Dm")
        pitch_classes = sorted(set(n % 12 for n in voicing))
        assert 2 in pitch_classes  # D
        assert 5 in pitch_classes  # F
        assert 9 in pitch_classes  # A

    def test_b_diminished_triad(self):
        """Bdim triad should contain B, D, F."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("Bdim")
        pitch_classes = sorted(set(n % 12 for n in voicing))
        assert 11 in pitch_classes  # B
        assert 2 in pitch_classes  # D
        assert 5 in pitch_classes  # F


class TestInversions:
    """Test first and second inversions."""

    def test_first_inversion_lowest_note(self):
        """First inversion of C major: E should be the lowest note."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C", inversion=1)
        # Lowest note pitch class should be E (4)
        assert voicing[0] % 12 == 4

    def test_second_inversion_lowest_note(self):
        """Second inversion of C major: G should be the lowest note."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C", inversion=2)
        # Lowest note pitch class should be G (7)
        assert voicing[0] % 12 == 7

    def test_root_position_lowest_note(self):
        """Root position of C major: C should be the lowest note."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C", inversion=0)
        assert voicing[0] % 12 == 0

    def test_first_inversion_still_has_all_pitches(self):
        """First inversion should still contain all chord tones."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("Am", inversion=1)
        pitch_classes = set(n % 12 for n in voicing)
        assert 9 in pitch_classes  # A
        assert 0 in pitch_classes  # C
        assert 4 in pitch_classes  # E

    def test_second_inversion_still_has_all_pitches(self):
        """Second inversion should still contain all chord tones."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("G", inversion=2)
        pitch_classes = set(n % 12 for n in voicing)
        assert 7 in pitch_classes  # G
        assert 11 in pitch_classes  # B
        assert 2 in pitch_classes  # D

    def test_inversion_notes_are_sorted(self):
        """Inverted voicings should still be sorted ascending."""
        vg = VoicingGenerator()
        for inv in [0, 1, 2]:
            voicing = vg.generate_voicing("C", inversion=inv)
            assert voicing == sorted(voicing), f"Inversion {inv} not sorted"


class TestVoiceLeading:
    """Test voice leading smoothness between consecutive chords."""

    def test_voice_leading_returns_correct_pitch_classes(self):
        """Voice-led voicing must contain the correct pitch classes."""
        vg = VoicingGenerator()
        prev = vg.generate_voicing("C")
        next_voicing = vg.apply_voice_leading(prev, "F")
        pitch_classes = set(n % 12 for n in next_voicing)
        assert 5 in pitch_classes  # F
        assert 9 in pitch_classes  # A
        assert 0 in pitch_classes  # C

    def test_voice_leading_minimizes_movement(self):
        """Voice-led voicing should have smaller total movement than naive root position."""
        vg = VoicingGenerator()
        prev = vg.generate_voicing("C")
        voice_led = vg.apply_voice_leading(prev, "F")
        naive = vg.generate_voicing("F")
        # Calculate total absolute movement
        # Both voicings should have same length for comparison
        min_len = min(len(prev), len(voice_led), len(naive))
        prev_trimmed = prev[:min_len]
        vl_movement = sum(abs(a - b) for a, b in zip(prev_trimmed, voice_led[:min_len]))
        naive_movement = sum(abs(a - b) for a, b in zip(prev_trimmed, naive[:min_len]))
        # Voice-led movement should be less than or equal to naive movement
        assert vl_movement <= naive_movement

    def test_voice_leading_c_to_g(self):
        """C -> G voice leading should produce smooth transition."""
        vg = VoicingGenerator()
        prev = vg.generate_voicing("C")
        next_voicing = vg.apply_voice_leading(prev, "G")
        # Maximum single-voice jump should be reasonable (within an octave)
        min_len = min(len(prev), len(next_voicing))
        for i in range(min_len):
            assert abs(prev[i] - next_voicing[i]) <= 12

    def test_voice_leading_preserves_note_count(self):
        """Voice leading should produce same number of notes as previous voicing."""
        vg = VoicingGenerator()
        prev = vg.generate_voicing("C")
        next_voicing = vg.apply_voice_leading(prev, "Am")
        assert len(next_voicing) == len(prev)

    def test_voice_leading_result_is_sorted(self):
        """Voice-led voicing should be sorted ascending."""
        vg = VoicingGenerator()
        prev = vg.generate_voicing("C")
        next_voicing = vg.apply_voice_leading(prev, "F")
        assert next_voicing == sorted(next_voicing)

    def test_voice_leading_common_tones_preserved(self):
        """Common tones between C and Am (C and E) should stay in place."""
        vg = VoicingGenerator()
        prev = vg.generate_voicing("C")
        next_voicing = vg.apply_voice_leading(prev, "Am")
        prev_pcs = set(n % 12 for n in prev)
        next_pcs = set(n % 12 for n in next_voicing)
        # C and Am share C(0) and E(4)
        common = prev_pcs & next_pcs
        assert 0 in common
        assert 4 in common


class TestRegisterConstraints:
    """Test that all voicing pitches fall within MIDI 36-84."""

    def test_all_notes_within_range(self):
        """All notes in any voicing should be between MIDI 36 and 84."""
        vg = VoicingGenerator()
        for chord in ["C", "D", "E", "F", "G", "A", "B",
                       "Cm", "Dm", "Em", "Fm", "Gm", "Am", "Bm"]:
            voicing = vg.generate_voicing(chord)
            for note in voicing:
                assert 36 <= note <= 84, (
                    f"Note {note} in {chord} voicing is out of range [36, 84]"
                )

    def test_inversions_within_range(self):
        """Inverted voicings should also stay within register constraints."""
        vg = VoicingGenerator()
        for inv in [0, 1, 2]:
            voicing = vg.generate_voicing("C", inversion=inv)
            for note in voicing:
                assert 36 <= note <= 84, (
                    f"Note {note} in C inversion {inv} is out of range"
                )

    def test_voice_led_voicing_within_range(self):
        """Voice-led voicings should remain in the valid register."""
        vg = VoicingGenerator()
        prev = vg.generate_voicing("C")
        for chord in ["F", "G", "Am", "Dm", "Em", "Bdim"]:
            next_voicing = vg.apply_voice_leading(prev, chord)
            for note in next_voicing:
                assert 36 <= note <= 84, (
                    f"Note {note} in voice-led {chord} is out of range"
                )
            prev = next_voicing

    def test_sharp_flat_chords_within_range(self):
        """Chords with sharps/flats should also be in range."""
        vg = VoicingGenerator()
        for chord in ["F#m", "Bb", "Eb", "C#m", "Ab"]:
            voicing = vg.generate_voicing(chord)
            for note in voicing:
                assert 36 <= note <= 84, (
                    f"Note {note} in {chord} voicing is out of range"
                )


class TestStyleSpecificVoicings:
    """Test style-specific voicing rules."""

    def test_jazz_voicing_has_extensions(self):
        """Jazz voicings should include extensions (7ths, 9ths, etc.)."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C", style="jazz")
        # Jazz voicings should have more than 3 notes (extensions)
        assert len(voicing) >= 4
        pitch_classes = set(n % 12 for n in voicing)
        # Should have the basic triad
        assert 0 in pitch_classes  # C
        assert 4 in pitch_classes  # E
        assert 7 in pitch_classes  # G
        # Should have at least a 7th (B=11 or Bb=10)
        assert 11 in pitch_classes or 10 in pitch_classes

    def test_pop_voicing_is_simple_triad(self):
        """Pop voicings should be simple triads (3 notes)."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C", style="pop")
        # Pop voicings should be simple: 3-4 notes (triad, possibly with doubled root)
        assert 3 <= len(voicing) <= 4

    def test_classical_voicing_has_four_parts(self):
        """Classical voicings should follow four-part harmony."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C", style="classical")
        # Classical four-part writing: exactly 4 notes
        assert len(voicing) == 4

    def test_soulful_voicing_has_extensions(self):
        """Soulful voicings should include 7ths or extensions."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C", style="soulful")
        assert len(voicing) >= 4

    def test_rnb_voicing_has_extensions(self):
        """RnB voicings should include 7ths or extended harmony."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C", style="rnb")
        assert len(voicing) >= 4

    def test_default_style_is_pop(self):
        """Default style should be pop (simple triad)."""
        vg = VoicingGenerator()
        default_voicing = vg.generate_voicing("C")
        pop_voicing = vg.generate_voicing("C", style="pop")
        # Same number of notes
        assert len(default_voicing) == len(pop_voicing)

    def test_jazz_minor_chord_voicing(self):
        """Jazz voicing for Am should include minor 7th."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("Am", style="jazz")
        pitch_classes = set(n % 12 for n in voicing)
        assert 9 in pitch_classes  # A
        assert 0 in pitch_classes  # C
        assert 4 in pitch_classes  # E
        # Minor 7th: G (7)
        assert 7 in pitch_classes

    def test_all_styles_within_register(self):
        """All style voicings should stay within MIDI 36-84."""
        vg = VoicingGenerator()
        for style in ["pop", "jazz", "classical", "soulful", "rnb"]:
            voicing = vg.generate_voicing("C", style=style)
            for note in voicing:
                assert 36 <= note <= 84, (
                    f"Note {note} in {style} style is out of range"
                )


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_seventh_chord_symbol(self):
        """Should handle seventh chord symbols like C7, Cmaj7."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("C7")
        pitch_classes = set(n % 12 for n in voicing)
        assert 0 in pitch_classes  # C
        assert 4 in pitch_classes  # E
        assert 7 in pitch_classes  # G
        assert 10 in pitch_classes  # Bb (dominant 7th)

    def test_major_seventh_chord_symbol(self):
        """Should handle Cmaj7."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("Cmaj7")
        pitch_classes = set(n % 12 for n in voicing)
        assert 0 in pitch_classes  # C
        assert 4 in pitch_classes  # E
        assert 7 in pitch_classes  # G
        assert 11 in pitch_classes  # B (major 7th)

    def test_invalid_chord_raises_error(self):
        """Invalid chord names should raise ValueError."""
        vg = VoicingGenerator()
        with pytest.raises(ValueError):
            vg.generate_voicing("XYZ123")

    def test_augmented_chord(self):
        """Should handle augmented chords."""
        vg = VoicingGenerator()
        voicing = vg.generate_voicing("Caug")
        pitch_classes = set(n % 12 for n in voicing)
        assert 0 in pitch_classes  # C
        assert 4 in pitch_classes  # E
        assert 8 in pitch_classes  # G#
