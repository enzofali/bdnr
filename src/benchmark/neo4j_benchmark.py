import statistics
import psutil
import time
from typing import Callable
from src.benchmark.dto import BenchmarkResult


def run_benchmark(query_id: str,
                  run_query: Callable[[], tuple],
                  duration: int = 60,
                  warmup: int = 5) -> BenchmarkResult:
    sys_cpu_pct, sys_mem_pct, wall_ms, driver_ms = [], [], [], []
    neo4j_mem_rss, major_faults = [], []

    # Find Neo4j process
    neo4j_proc = next(
        (p for p in psutil.process_iter(['name'])
         if 'neo4j' in (p.info['name'] or '').lower()),
        None
    )

    psutil.cpu_percent(None)
    if neo4j_proc:
        neo4j_proc.cpu_percent(None)
        prev_pageins = neo4j_proc.memory_info().pageins
    else:
        prev_pageins = 0

    # Warmup
    for _ in range(warmup):
        run_query()

    success_count = 0
    errors = []
    t_end = time.time() + duration

    while time.time() < t_end:
        start_time = time.perf_counter_ns()
        try:
            result, driver_time_ns = run_query()

            wall_time_ns = time.perf_counter_ns() - start_time
            wall_ms.append(wall_time_ns / 1_000_000)  # Convert to ms
            driver_ms.append(driver_time_ns / 1_000_000)
            success_count += 1
        except Exception as e:
            errors.append(str(e))

        # System resource monitoring
        sys_cpu_pct.append(psutil.cpu_percent(interval=None, percpu=False))
        sys_mem_pct.append(psutil.virtual_memory().percent)

        # Neo4j process monitoring
        if neo4j_proc and neo4j_proc.is_running():
            mem_info = neo4j_proc.memory_info()
            neo4j_mem_rss.append(mem_info.rss / 1024 ** 2)  # MB

            cur_pageins = neo4j_proc.memory_info().pageins
            major_faults.append(max(0, cur_pageins - prev_pageins))
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
        "neo4j_rss_avg_mb": statistics.mean(neo4j_mem_rss) if neo4j_mem_rss else 0,
        "neo4j_rss_p95_mb": statistics.quantiles(neo4j_mem_rss, n=20)[-1] if neo4j_mem_rss and len(
            neo4j_mem_rss) >= 5 else 0,
        "neo4j_rss_p99_mb": statistics.quantiles(neo4j_mem_rss, n=100)[-1] if neo4j_mem_rss and len(
            neo4j_mem_rss) >= 5 else 0,
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
            "neo4j_rss_mb": neo4j_mem_rss,
        }
    )
