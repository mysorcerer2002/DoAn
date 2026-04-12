"""CLI runner — chạy job thủ công cho debug.

Usage:
    python -m app.jobs.run_once cleanup_codes
"""

import asyncio
import sys

JOBS = {
    "cleanup_codes": "app.jobs.cleanup_codes:cleanup_expired_verification_codes",
    "birthday": "app.jobs.birthday_voucher:birthday_voucher_job",
}


async def run_job(job_name: str) -> None:
    """Chạy 1 job cụ thể."""
    if job_name not in JOBS:
        print(f"Unknown job: {job_name}")
        print(f"Available jobs: {', '.join(JOBS.keys())}")
        sys.exit(1)

    module_path, func_name = JOBS[job_name].rsplit(":", 1)
    import importlib

    module = importlib.import_module(module_path)
    func = getattr(module, func_name)
    result = await func()
    print(f"Job '{job_name}' completed. Result: {result}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python -m app.jobs.run_once <job_name>")
        print(f"Available jobs: {', '.join(JOBS.keys())}")
        sys.exit(1)

    asyncio.run(run_job(sys.argv[1]))
