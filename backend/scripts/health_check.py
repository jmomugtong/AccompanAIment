"""Health check script for all service dependencies.

Tests connectivity to PostgreSQL, Redis, and Ollama. Returns exit
code 0 if all checks pass, 1 if any fail. Idempotent and safe to
run repeatedly.
"""

import argparse
import sys
import time


def check_postgres(database_url: str, timeout: int = 5) -> bool:
    """Test PostgreSQL connectivity.

    Args:
        database_url: Sync database URL.
        timeout: Connection timeout in seconds.

    Returns:
        True if the connection succeeds.
    """
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(
            database_url,
            connect_args={"connect_timeout": timeout},
        )
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        engine.dispose()
        return True
    except Exception as exc:
        print(f"  PostgreSQL check failed: {exc}")
        return False


def check_redis(redis_url: str, timeout: int = 5) -> bool:
    """Test Redis connectivity.

    Args:
        redis_url: Redis connection URL.
        timeout: Connection timeout in seconds.

    Returns:
        True if PING succeeds.
    """
    try:
        import redis

        client = redis.from_url(redis_url, socket_timeout=timeout)
        response = client.ping()
        client.close()
        return bool(response)
    except Exception as exc:
        print(f"  Redis check failed: {exc}")
        return False


def check_ollama(ollama_url: str, timeout: int = 10) -> bool:
    """Test Ollama LLM server connectivity.

    Args:
        ollama_url: Base URL for the Ollama server.
        timeout: Request timeout in seconds.

    Returns:
        True if the Ollama API responds.
    """
    try:
        import urllib.request

        url = ollama_url.rstrip("/") + "/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception as exc:
        print(f"  Ollama check failed: {exc}")
        return False


def run_health_checks(
    database_url: str,
    redis_url: str,
    ollama_url: str,
    timeout: int = 5,
    verbose: bool = False,
) -> dict[str, bool]:
    """Run all health checks and return results.

    Args:
        database_url: Sync PostgreSQL URL.
        redis_url: Redis URL.
        ollama_url: Ollama base URL.
        timeout: Per-service timeout in seconds.
        verbose: Print timing information.

    Returns:
        Dict mapping service name to pass/fail boolean.
    """
    results: dict[str, bool] = {}

    services = [
        ("PostgreSQL", lambda: check_postgres(database_url, timeout)),
        ("Redis", lambda: check_redis(redis_url, timeout)),
        ("Ollama", lambda: check_ollama(ollama_url, timeout)),
    ]

    for name, check_fn in services:
        start = time.time()
        ok = check_fn()
        elapsed = time.time() - start
        results[name] = ok

        status = "OK" if ok else "FAIL"
        timing = f" ({elapsed:.2f}s)" if verbose else ""
        print(f"  [{status}] {name}{timing}")

    return results


def main() -> None:
    """CLI entry point for health checks."""
    parser = argparse.ArgumentParser(
        description="Test connectivity to all service dependencies (DB, Redis, Ollama)."
    )
    parser.add_argument(
        "--database-url",
        default="postgresql://accompaniment:accompaniment@localhost:5432/accompaniment",
        help="Sync PostgreSQL database URL",
    )
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379/0",
        help="Redis connection URL",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama LLM server base URL",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Per-service connection timeout in seconds (default: 5)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print timing information for each check",
    )
    args = parser.parse_args()

    print("Running health checks...")
    results = run_health_checks(
        database_url=args.database_url,
        redis_url=args.redis_url,
        ollama_url=args.ollama_url,
        timeout=args.timeout,
        verbose=args.verbose,
    )

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nResult: {passed}/{total} services healthy.")

    if passed < total:
        failed = [name for name, ok in results.items() if not ok]
        print(f"Failed services: {', '.join(failed)}")
        sys.exit(1)

    print("All services are healthy.")
    sys.exit(0)


if __name__ == "__main__":
    main()
