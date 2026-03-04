"""Benchmark pipeline latency for key operations.

Measures execution time for chord parsing, voicing generation,
MIDI generation, and overall pipeline throughput. All benchmarks
run locally without requiring external services.
"""

import argparse
import statistics
import sys
import time


def benchmark_chord_parsing(iterations: int) -> dict:
    """Benchmark chord progression parsing.

    Args:
        iterations: Number of iterations to run.

    Returns:
        Dict with timing statistics.
    """
    from src.music.chord_parser import ChordParser

    parser = ChordParser()
    progressions = [
        "C | F | G | C",
        "Dm7 | G7 | Cmaj7 | Am7",
        "Am | F | C | G",
        "C | Em | F | G | Am | Dm | G | C",
    ]

    timings = []
    for i in range(iterations):
        prog = progressions[i % len(progressions)]
        start = time.perf_counter()
        parser.parse_progression(prog)
        elapsed = time.perf_counter() - start
        timings.append(elapsed)

    return _compute_stats("chord_parsing", timings)


def benchmark_voicing_generation(iterations: int) -> dict:
    """Benchmark chord voicing generation across styles.

    Args:
        iterations: Number of iterations to run.

    Returns:
        Dict with timing statistics.
    """
    from src.music.voicing_generator import VoicingGenerator

    generator = VoicingGenerator()
    chords = ["C", "Am", "F", "G", "Dm7", "Cmaj7", "Em", "Bdim"]
    styles = ["pop", "jazz", "classical", "soulful", "rnb"]

    timings = []
    for i in range(iterations):
        chord = chords[i % len(chords)]
        style = styles[i % len(styles)]
        start = time.perf_counter()
        generator.generate_voicing(chord, style=style)
        elapsed = time.perf_counter() - start
        timings.append(elapsed)

    return _compute_stats("voicing_generation", timings)


def benchmark_midi_generation(iterations: int) -> dict:
    """Benchmark MIDI score creation (in-memory, no file I/O).

    Args:
        iterations: Number of iterations to run.

    Returns:
        Dict with timing statistics.
    """
    from src.music.midi_generator import MIDIGenerator

    melody_notes = [60, 62, 64, 65, 67, 65, 64, 62]
    melody_durations = [1.0] * 8
    voicings = [[48, 52, 55], [53, 57, 60], [55, 59, 62], [48, 52, 55]]
    voicing_durations = [2.0] * 4

    timings = []
    for _ in range(iterations):
        start = time.perf_counter()
        gen = MIDIGenerator(tempo=120, time_signature=(4, 4))
        gen.create_score()
        gen.add_melody_track(melody_notes, melody_durations)
        gen.add_accompaniment_track(voicings, voicing_durations)
        elapsed = time.perf_counter() - start
        timings.append(elapsed)

    return _compute_stats("midi_generation", timings)


def benchmark_full_pipeline(iterations: int) -> dict:
    """Benchmark the full in-memory pipeline (parse + voice + MIDI).

    Args:
        iterations: Number of iterations to run.

    Returns:
        Dict with timing statistics.
    """
    from src.music.chord_parser import ChordParser
    from src.music.midi_generator import MIDIGenerator
    from src.music.voicing_generator import VoicingGenerator

    parser = ChordParser()
    voicer = VoicingGenerator()

    progression_text = "C | Am | F | G"
    melody_notes = [60, 62, 64, 65, 67, 65, 64, 62]
    melody_durations = [1.0] * 8

    timings = []
    for _ in range(iterations):
        start = time.perf_counter()

        # Parse chords
        result = parser.parse_progression(progression_text)

        # Generate voicings
        voicings = [voicer.generate_voicing(c, style="jazz") for c in result.chords]
        durations = [2.0] * len(voicings)

        # Build MIDI score
        gen = MIDIGenerator(tempo=120, time_signature=(4, 4))
        gen.create_score()
        gen.add_melody_track(melody_notes, melody_durations)
        gen.add_accompaniment_track(voicings, durations)

        elapsed = time.perf_counter() - start
        timings.append(elapsed)

    return _compute_stats("full_pipeline", timings)


def _compute_stats(name: str, timings: list[float]) -> dict:
    """Compute timing statistics from a list of measurements.

    Args:
        name: Benchmark name.
        timings: List of elapsed times in seconds.

    Returns:
        Dict with name, count, min, max, mean, median, p95, p99.
    """
    timings_sorted = sorted(timings)
    count = len(timings_sorted)

    p95_idx = int(count * 0.95)
    p99_idx = int(count * 0.99)

    return {
        "name": name,
        "iterations": count,
        "min_ms": round(min(timings_sorted) * 1000, 3),
        "max_ms": round(max(timings_sorted) * 1000, 3),
        "mean_ms": round(statistics.mean(timings_sorted) * 1000, 3),
        "median_ms": round(statistics.median(timings_sorted) * 1000, 3),
        "p95_ms": round(timings_sorted[min(p95_idx, count - 1)] * 1000, 3),
        "p99_ms": round(timings_sorted[min(p99_idx, count - 1)] * 1000, 3),
        "total_s": round(sum(timings_sorted), 3),
    }


def print_results(results: list[dict]) -> None:
    """Print benchmark results in a formatted table.

    Args:
        results: List of stats dictionaries from _compute_stats.
    """
    header = (
        f"{'Benchmark':<25} {'Iters':>6} {'Min(ms)':>10} {'Mean(ms)':>10} "
        f"{'Median(ms)':>10} {'P95(ms)':>10} {'P99(ms)':>10} {'Total(s)':>10}"
    )
    print(header)
    print("-" * len(header))

    for r in results:
        print(
            f"{r['name']:<25} {r['iterations']:>6} {r['min_ms']:>10.3f} "
            f"{r['mean_ms']:>10.3f} {r['median_ms']:>10.3f} {r['p95_ms']:>10.3f} "
            f"{r['p99_ms']:>10.3f} {r['total_s']:>10.3f}"
        )


def main() -> None:
    """CLI entry point for performance benchmarks."""
    parser = argparse.ArgumentParser(
        description="Benchmark pipeline latency for key operations."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of iterations per benchmark (default: 100)",
    )
    parser.add_argument(
        "--benchmark",
        choices=["chord_parsing", "voicing", "midi", "full_pipeline", "all"],
        default="all",
        help="Which benchmark to run (default: all)",
    )
    args = parser.parse_args()

    # Add backend/src to path so imports work when run from project root.
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    benchmarks = {
        "chord_parsing": benchmark_chord_parsing,
        "voicing": benchmark_voicing_generation,
        "midi": benchmark_midi_generation,
        "full_pipeline": benchmark_full_pipeline,
    }

    if args.benchmark == "all":
        selected = list(benchmarks.keys())
    else:
        selected = [args.benchmark]

    print(f"Running benchmarks ({args.iterations} iterations each)...\n")

    results = []
    for name in selected:
        try:
            result = benchmarks[name](args.iterations)
            results.append(result)
        except Exception as exc:
            print(f"FAILED: {name} -- {exc}")
            sys.exit(1)

    print_results(results)
    print("\nBenchmark complete.")


if __name__ == "__main__":
    main()
