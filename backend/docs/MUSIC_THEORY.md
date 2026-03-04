# Music Theory Reference

This document describes the music theory concepts underlying
AccompanAIment's piano accompaniment generation, including chord voicing
strategies for each supported style, voice leading rules, and the CREPE
pitch detection system used for melody extraction.

## Table of Contents

- [Chord Voicing Strategies by Style](#chord-voicing-strategies-by-style)
- [Voice Leading Rules](#voice-leading-rules)
- [CREPE Pitch Detection](#crepe-pitch-detection)
- [Chord Progression Conventions](#chord-progression-conventions)
- [Key and Scale Reference](#key-and-scale-reference)

## Chord Voicing Strategies by Style

Each accompaniment style uses a distinct set of voicing techniques,
register choices, and harmonic extensions. The LLM agent receives these
guidelines as part of its system prompt when generating music21 voicing
code.

### Jazz

**Characteristic features:**
- Extended harmony: 7ths, 9ths, 11ths, and 13ths are standard.
- Shell voicings: root, 3rd, and 7th in the left hand; extensions and
  color tones in the right hand.
- Rootless voicings: omit the root (assumed played by a bassist) and
  voice the 3rd, 7th, and upper extensions.
- Drop-2 voicings: take a close-position four-note chord and drop the
  second-highest note down an octave for a wider, more pianistic spread.
- Tritone substitution: replace a dominant V7 chord with a dominant
  chord a tritone away for chromatic bass motion.

**Register:** Left hand in C3-C4 range; right hand in C4-C6 range.

**Rhythm:** Swing eighth notes. Comping patterns with syncopated attacks
on beats 2 and 4 or the "and" of beat 2.

**Example voicing for Cmaj7:**
```
Right hand: E4 - G4 - B4 - D5  (3rd, 5th, 7th, 9th)
Left hand:  C3 - E3             (root, 3rd)
```

### Soulful

**Characteristic features:**
- Warm, gospel-influenced voicings with thick, close-position chords.
- Frequent use of suspended chords (sus2, sus4) that resolve.
- Minor 7th and major 7th chords with added 9ths for richness.
- Grace notes and passing tones to create an expressive, vocal quality.
- Dynamic contrast: soft verses, powerful choruses.

**Register:** Full piano range. Left hand provides root and 5th in
octaves (C2-C3); right hand voices upper structure in C4-C5.

**Rhythm:** Straight eighth notes with occasional triplet fills.
Emphasis on beats 2 and 4 (backbeat feel).

**Example voicing for Am7:**
```
Right hand: C4 - E4 - G4 - B4  (minor 3rd, 5th, 7th, 9th relative to A)
Left hand:  A2 - A3             (root octave)
```

### RnB

**Characteristic features:**
- Rich extended voicings: 9ths, 11ths, and altered tones (sharp 9,
  sharp 11, flat 13) are common.
- Neo-soul influence: major 7th chords with added 9ths and 13ths.
- Smooth voice leading with minimal movement between chords.
- Stacked fourths and quartal voicings for a modern, open sound.
- Left hand often plays broken patterns (arpeggiated roots and 5ths).

**Register:** Left hand in C2-C3; right hand clusters in C4-C5 range
for intimate, close voicings.

**Rhythm:** Straight 16th-note subdivisions. Syncopated comping with
ghost notes and anticipated chord changes.

**Example voicing for Fmaj9:**
```
Right hand: A4 - C5 - E5 - G5  (3rd, 5th, 7th, 9th)
Left hand:  F2 - C3             (root, 5th)
```

### Pop

**Characteristic features:**
- Clean triads and simple inversions. Avoid excessive extensions.
- Power chord feel: root-5th-octave patterns in the left hand.
- Arpeggiated patterns (broken chords) are common.
- Rhythmic consistency: steady eighth-note or quarter-note patterns.
- Support the vocal melody without competing for attention.

**Register:** Centered in the middle of the piano (C3-C5) to stay
out of the vocal range.

**Rhythm:** Straight eighth notes. Consistent rhythmic patterns
that repeat each bar. Occasionally syncopated for emphasis.

**Example voicing for G major:**
```
Right hand: B3 - D4 - G4       (3rd, 5th, root)
Left hand:  G2 - D3             (root, 5th)
```

### Classical

**Characteristic features:**
- Four-part SATB (soprano, alto, tenor, bass) voice leading.
- Proper doubling rules: double the root in root position, avoid
  doubling the leading tone.
- Smooth part motion: each voice moves by step or stays on the same
  note when possible.
- Avoid parallel 5ths and parallel octaves between any two voices.
- Common-tone retention: keep shared notes between consecutive chords
  in the same voice.
- Cadential patterns: authentic (V-I), plagal (IV-I), half (any-V),
  and deceptive (V-vi) cadences.

**Register:** Bass voice in C2-C3; tenor in C3-C4; alto in C4-C5;
soprano in C4-C6. Voices should not cross registers.

**Rhythm:** Follows the meter strictly. Hymn-like block chords or
Alberti bass patterns (broken chord accompaniment in left hand).

**Example voicing for C major (root position):**
```
Soprano: G4
Alto:    E4
Tenor:   C4
Bass:    C3
```

## Voice Leading Rules

Voice leading governs how individual notes move from one chord to the
next. Good voice leading creates smooth, connected harmonic motion.
These rules apply to all styles but are enforced most strictly in the
classical style.

### Core Principles

1. **Minimal motion:** Each voice should move to the nearest available
   chord tone. Leaps larger than a 4th should be followed by stepwise
   motion in the opposite direction.

2. **Common tones:** When two consecutive chords share a note, keep it
   in the same voice and register.

3. **Contrary motion:** When the bass moves up, prefer inner voices to
   move down (and vice versa). This creates a balanced, full sound.

4. **Stepwise motion:** Prefer stepwise (scale-degree) motion over
   leaps. Smooth motion in all voices is the primary goal.

### Forbidden Parallels

- **Parallel 5ths:** Two voices moving in parallel motion and
  maintaining a perfect 5th interval. Sounds hollow and undermines
  voice independence.

- **Parallel octaves:** Two voices moving in parallel at the octave.
  Reduces the effective number of independent voices.

- **Hidden (direct) 5ths and octaves:** Two voices moving in similar
  motion to a perfect 5th or octave, where the upper voice leaps.
  Acceptable only when the upper voice moves by step.

### Resolution Rules

- **Leading tone (scale degree 7):** Must resolve up by half step to
  the tonic (scale degree 1) in the soprano voice. In inner voices,
  the leading tone may resolve down to the 5th of the tonic chord.

- **Chordal 7th:** Must resolve down by step. In a V7-I progression,
  the 7th of V resolves to the 3rd of I.

- **Augmented intervals:** Avoid melodic augmented intervals (e.g.,
  augmented 2nd, augmented 4th) in any single voice.

### Style-Specific Relaxations

- **Jazz and RnB:** Parallel motion is acceptable and sometimes
  desirable (e.g., parallel major 7th chords sliding chromatically).
  The emphasis is on color and groove over strict independence.

- **Pop:** Voice independence is less critical. Block chord movement
  and parallel triads are common and stylistically appropriate.

- **Soulful:** Follows gospel conventions where parallel 3rds and
  6ths are encouraged for warmth. Passing tones and suspensions
  are freely used.

## CREPE Pitch Detection

CREPE (Convolutional Representation for Pitch Estimation) is the deep
learning model used by AccompanAIment to extract vocal melodies from
uploaded audio files.

### How CREPE Works

1. **Input:** Raw audio waveform, resampled to 16 kHz (mono).

2. **Framing:** The audio is divided into overlapping frames. Each
   frame is 1024 samples (64 ms at 16 kHz) with a hop size of 10 ms.

3. **Neural network:** A 6-layer convolutional neural network processes
   each frame. The network was trained on a large dataset of
   synthesized audio with known ground-truth pitches.

4. **Output per frame:**
   - **Pitch (Hz):** The estimated fundamental frequency, mapped to
     360 bins spanning 6 octaves (C1 to B7, 32.70 Hz to 1975.5 Hz).
   - **Confidence (0-1):** The network's confidence that the frame
     contains a pitched (voiced) signal rather than silence or noise.

5. **Post-processing:** Frames with confidence below a threshold
   (default 0.5) are marked as unvoiced. The resulting pitch contour
   is smoothed with a median filter to reduce octave errors.

### Model Capacities

CREPE offers multiple model sizes that trade accuracy for speed:

| Capacity | Parameters | Relative Speed | Accuracy |
|----------|-----------|----------------|----------|
| tiny     | 13K       | Fastest        | Lowest   |
| small    | 53K       | Fast           | Low      |
| medium   | 210K      | Moderate       | Good     |
| large    | 839K      | Slow           | High     |
| full     | 3.3M      | Slowest        | Highest  |

AccompanAIment uses the `full` model by default for maximum accuracy.
This can be changed via the `CREPE_MODEL_CAPACITY` environment variable.

### Integration in AccompanAIment

1. The user uploads an audio file (MP3, WAV, M4A, or FLAC).
2. The audio is preprocessed: converted to mono, resampled to 22.05 kHz
   (for librosa compatibility), and normalized.
3. CREPE processes the audio and returns pitch, confidence, and
   timestamp arrays.
4. The pitch contour is stored in the `melodies` table as a JSONB field.
5. The melody data is cached in Redis with a 7-day TTL to avoid
   reprocessing the same song.

### Limitations

- CREPE is designed for monophonic (single-voice) pitch detection. It
  works best on isolated vocals or strongly dominant melodies.
- Polyphonic audio (multiple instruments playing simultaneously) may
  confuse the model, leading to octave errors or spurious pitch jumps.
- Very breathy or whispered vocals produce low confidence scores and
  may be classified as unvoiced.
- Processing time scales linearly with audio duration. A 5-minute song
  at full capacity takes approximately 30-60 seconds on a modern GPU.

## Chord Progression Conventions

AccompanAIment accepts chord progressions as pipe-separated strings.
Each chord occupies one beat group (typically one bar in 4/4 time).

### Input Format

```
Dm7 | G7 | Cmaj7 | Am7
```

### Supported Chord Symbols

The system uses music21 for chord parsing and supports standard
chord notation:

| Symbol     | Meaning                         | Example      |
|------------|---------------------------------|--------------|
| C          | Major triad                     | C E G        |
| Cm         | Minor triad                     | C Eb G       |
| Cdim       | Diminished triad                | C Eb Gb      |
| Caug       | Augmented triad                 | C E G#       |
| C7         | Dominant 7th                    | C E G Bb     |
| Cmaj7      | Major 7th                       | C E G B      |
| Cm7        | Minor 7th                       | C Eb G Bb    |
| Cdim7      | Diminished 7th                  | C Eb Gb Bbb  |
| Cm7b5      | Half-diminished 7th             | C Eb Gb Bb   |
| Csus2      | Suspended 2nd                   | C D G        |
| Csus4      | Suspended 4th                   | C F G        |
| Cadd9      | Added 9th                       | C E G D      |
| C9         | Dominant 9th                    | C E G Bb D   |
| Cmaj9      | Major 9th                       | C E G B D    |
| Cm9        | Minor 9th                       | C Eb G Bb D  |
| C11        | Dominant 11th                   | C E G Bb D F |
| C13        | Dominant 13th                   | C E G Bb D A |

### Slash Chords

Bass notes can be specified with a slash:

```
C/E | F/A | G/B | C
```

The note after the slash is played as the lowest voice.

## Key and Scale Reference

The system supports generation in any of the 12 major and 12 minor keys.
The LLM agent transposes voicing patterns to the requested key.

### Major Scales

| Key | Notes                       |
|-----|-----------------------------|
| C   | C D E F G A B               |
| G   | G A B C D E F#              |
| D   | D E F# G A B C#             |
| A   | A B C# D E F# G#            |
| E   | E F# G# A B C# D#           |
| B   | B C# D# E F# G# A#          |
| F   | F G A Bb C D E              |
| Bb  | Bb C D Eb F G A             |
| Eb  | Eb F G Ab Bb C D            |
| Ab  | Ab Bb C Db Eb F G           |
| Db  | Db Eb F Gb Ab Bb C          |
| Gb  | Gb Ab Bb Cb Db Eb F         |

### Natural Minor Scales

| Key | Notes                       |
|-----|-----------------------------|
| Am  | A B C D E F G               |
| Em  | E F# G A B C D              |
| Bm  | B C# D E F# G A             |
| F#m | F# G# A B C# D E            |
| C#m | C# D# E F# G# A B           |
| G#m | G# A# B C# D# E F#          |
| Dm  | D E F G A Bb C              |
| Gm  | G A Bb C D Eb F             |
| Cm  | C D Eb F G Ab Bb            |
| Fm  | F G Ab Bb C Db Eb           |
| Bbm | Bb C Db Eb F Gb Ab          |
| Ebm | Eb F Gb Ab Bb Cb Db         |

### Modes Used in Accompaniment

| Mode       | Scale Pattern (relative to major) | Common Styles     |
|------------|-----------------------------------|-------------------|
| Ionian     | 1 2 3 4 5 6 7                     | Pop, classical    |
| Dorian     | 1 2 b3 4 5 6 b7                  | Jazz, soul        |
| Mixolydian | 1 2 3 4 5 6 b7                   | Blues, rock, pop  |
| Aeolian    | 1 2 b3 4 5 b6 b7                 | RnB, pop ballads  |
| Lydian     | 1 2 3 #4 5 6 7                   | Jazz, film scores |
| Blues      | 1 b3 4 b5 5 b7                   | Blues, jazz, RnB  |
