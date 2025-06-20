import statistics
import time
from typing import Callable

import psutil

from src.benchmark.dto import BenchmarkResult
from src.benchmark.mongo_listener import BenchListener


def run_benchmark(query_id: str,
                  run_query: Callable[[], object],
                  listener: BenchListener,
                  duration: int = 60,
                  warmup=5) -> BenchmarkResult:
    sys_cpu_pct, sys_mem_pct, wall_ms, driver_ms = [], [], [], []
    mongo_mem_rss, major_faults = [], []

    mongo_proc = next(
        (p for p in psutil.process_iter(['name'])
         if 'mongod' in (p.info['name'] or '').lower()),
        None
    )

    psutil.cpu_percent(None)
    if mongo_proc:
        mongo_proc.cpu_percent(None)
        prev_pageins = mongo_proc.memory_info().pageins
    else:
        prev_pageins = 0

    # Warmup (caches and JITs stabilise)
    for _ in range(warmup):
        run_query()

    success_count = 0
    errors = []
    t_end = time.time() + duration

    while time.time() < t_end:
        try:
            result, elapsed_time = run_query()
            # end-to-end latency (with client-side overhead)
            wall_ms.append(elapsed_time / 1_000_000)
            success_count += 1
        except Exception as e:
            errors.append(str(e))

        # server + network latency
        driver_ms.append(sum(listener.latencies) / 1000)
        listener.latencies.clear()

        sys_cpu_pct.append(psutil.cpu_percent(interval=None, percpu=False))
        sys_mem_pct.append(psutil.virtual_memory().percent)

        if mongo_proc and mongo_proc.is_running():
            mem_info = mongo_proc.memory_info()
            mongo_mem_rss.append(mem_info.rss / 1024 ** 2)  # MB

            cur_pageins = mongo_proc.memory_info().pageins
            major_faults.append(max(0, cur_pageins - prev_pageins))  # avoid negatives
            prev_pageins = cur_pageins

        # throttles the loop, WARING bias in throughput measure
        time.sleep(0.05)

    stats = {
        "query": query_id,
        "duration": duration,
        "iterations": len(wall_ms),
        "successes": success_count,
        "errors": len(errors),

        # Wall time metrics
        "wall_avg_ms": statistics.mean(wall_ms) if wall_ms else 0,
        "wall_p95_ms": statistics.quantiles(wall_ms, n=20)[-1] if wall_ms and len(wall_ms) >= 5 else 0,
        "wall_p99_ms": statistics.quantiles(wall_ms, n=100)[-1] if wall_ms and len(wall_ms) >= 5 else 0,

        # Driver time metrics
        "driver_avg_ms": statistics.mean(driver_ms) if driver_ms else 0,
        "driver_p95_ms": statistics.quantiles(driver_ms, n=20)[-1] if driver_ms and len(driver_ms) >= 5 else 0,
        "driver_p99_ms": statistics.quantiles(driver_ms, n=100)[-1] if driver_ms and len(driver_ms) >= 5 else 0,

        # System metrics
        "cpu_avg_pct": statistics.mean(sys_cpu_pct) if sys_cpu_pct else 0,
        "cpu_p95_pct": statistics.quantiles(sys_cpu_pct, n=20)[-1] if sys_cpu_pct and len(sys_cpu_pct) >= 5 else 0,
        "cpu_p99_pct": statistics.quantiles(sys_cpu_pct, n=100)[-1] if sys_cpu_pct and len(sys_cpu_pct) >= 5 else 0,
        "sys_mem_avg_pct": statistics.mean(sys_mem_pct) if sys_mem_pct else 0,
        "sys_mem_p95_pct": statistics.quantiles(sys_mem_pct, n=20)[-1] if sys_mem_pct and len(sys_mem_pct) >= 5 else 0,
        "sys_mem_p99_pct": statistics.quantiles(sys_mem_pct, n=100)[-1] if sys_mem_pct and len(sys_mem_pct) >= 5 else 0,
        "rss_avg_mb": statistics.mean(mongo_mem_rss) if mongo_mem_rss else 0,
        "rss_p95_mb": statistics.quantiles(mongo_mem_rss, n=20)[-1] if mongo_mem_rss and len(
            mongo_mem_rss) >= 5 else 0,
        "rss_p99_mb": statistics.quantiles(mongo_mem_rss, n=100)[-1] if mongo_mem_rss and len(
            mongo_mem_rss) >= 5 else 0,
        "major_faults_per_sec": sum(major_faults) / duration if duration > 0 else 0,
        "throughput_qps": len(wall_ms) / duration if duration > 0 else 0
    }

    return BenchmarkResult(
        summary=stats,
        series={
            "wall_ms": wall_ms,
            "driver_ms": driver_ms,
            "sys_cpu_pct": sys_cpu_pct,
            "sys_mem_pct": sys_mem_pct,
            "mongo_rss_mb": mongo_mem_rss,
        }
    )
