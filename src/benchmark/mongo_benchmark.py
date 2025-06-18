import statistics
import time
import random
from dataclasses import dataclass
from typing import Callable, Dict, List

import psutil
from pymongo.cursor import Cursor

from src.benchmark.mongo_listener import BenchListener


@dataclass
class BenchmarkResult:
    summary: Dict[str, float]
    series: Dict[str, List[float]]


GENRES = [
    "Adventure", "Animation", "Children", "Comedy", "Fantasy", "Action",
    "Drama", "Horror", "Sci-Fi", "Romance", "Thriller"
]

TAG_VOCAB = [
    "animated", "cgi", "classic", "pixar", "disney", "heartwarming", "kids",
    "fun", "friendship", "great movie", "story", "nostalgic", "imdb top 250"
]

RATING_VALUES = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]


def generate_rand_movie_doc(movie_id: int) -> dict:
    num_ratings = random.randint(30, 120)
    ratings = [
        {
            "userId": random.randint(1, 1_000),
            "rating": round(random.choice(RATING_VALUES), 1),
            "timestamp": int(time.time()) - random.randint(0, 10**7)
        }
        for _ in range(num_ratings)
    ]

    # Rating distribution
    rating_distribution = {f"{r:.1f}": 0 for r in RATING_VALUES}
    for rating in ratings:
        rating_distribution[f"{rating['rating']:.1f}"] += 1

    avg_rating = round(sum(rating["rating"] for rating in ratings) / len(ratings), 2)

    return {
        "movieId": movie_id,
        "title": f"Random Movie {movie_id}",
        "year": random.randint(1950, 2025),
        "genres": random.sample(GENRES, k=random.randint(2, 5)),
        "ratings": ratings,
        "tagGenome": [
            {
                "tagId": tid,
                "tag": TAG_VOCAB[tid % len(TAG_VOCAB)],
                "relevance": round(random.uniform(0.75, 1.0), 5)
            }
            for tid in [random.randint(1, 1000) for _ in range(random.randint(10, 20))]
        ],
        "stats": {
            "ratingCount": num_ratings,
            "avgRating": avg_rating,
            "ratingDistribution": rating_distribution
        }
    }


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
            if isinstance(result, Cursor):
                list(result)  # force materialization
            # end-to-end latency (with client-side overhead)
            wall_ms.append(elapsed_time / 1_000_000)
            success_count += 1
        except Exception as e:
            # print(e)
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
        "wall_avg_ms": statistics.mean(wall_ms) if wall_ms else 0,
        "driver_avg_ms": statistics.mean(driver_ms) if driver_ms else 0,
        "cpu_avg_pct": statistics.mean(sys_cpu_pct) if sys_cpu_pct else 0,
        "rss_avg_mb": statistics.mean(mongo_mem_rss) if mongo_mem_rss else 0,
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
