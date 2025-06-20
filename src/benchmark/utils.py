import platform
import random
import time
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import psutil


GENRES = [
    "Adventure", "Animation", "Children", "Comedy", "Fantasy", "Action",
    "Drama", "Horror", "Sci-Fi", "Romance", "Thriller"
]

TAG_VOCAB = [
    "animated", "cgi", "classic", "pixar", "disney", "heartwarming", "kids",
    "fun", "friendship", "great movie", "story", "nostalgic", "imdb top 250"
]

RATING_VALUES = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]


def timed_op(func):
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter_ns()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter_ns() - t0) / 1_000_000  # ms
        return result, elapsed
    return wrapper


def get_system_info() -> Dict[str, Any]:
    system_info = {
        "python_version": platform.python_version(),
        "system": {
            "os": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "cpu": {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "frequency_mhz": psutil.cpu_freq().current,
        },
        "memory": {
            "total_ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            "available_ram_gb": round(psutil.virtual_memory().available / (1024 ** 3), 2),
        }
    }
    return system_info


def plot_benchmark_results(
        query_name: str,
        cpu_usage: List[float],
        wall_latency_ms: List[float],
        memory_usage: List[float],
        driver_latency_ms: List[float],
        mongo_mem: List[float] = None,
        neo4j_mem: List[float] = None
):
    metrics = [
        ('CPU Usage (%)', cpu_usage, 'blue'),
        ('System Memory Usage (%)', memory_usage, 'green'),
        ('Wall Latency (ms)', wall_latency_ms, 'red'),
        ('Driver Latency (ms)', driver_latency_ms, 'orange'),
    ]

    if mongo_mem:
        metrics.append(('MongoDB Memory (MB)', mongo_mem, 'purple'))

    if neo4j_mem:
        metrics.append(('neo4j Memory (MB)', neo4j_mem, 'purple'))

    num_plots = len(metrics)
    cols = 2
    rows = (num_plots + 1) // 2

    fig, axes = plt.subplots(rows, cols, figsize=(12, 3.5 * rows))
    axes = axes.flatten()

    for idx, (title, data, color) in enumerate(metrics):
        axes[idx].plot(data, color=color)
        axes[idx].set_xlabel('Iteration')
        axes[idx].set_ylabel(title)
        axes[idx].set_title(f'{title} - {query_name}')
        axes[idx].grid(True)

    for j in range(len(metrics), len(axes)):
        fig.delaxes(axes[j])

    fig.suptitle(f"Benchmark Results - {query_name}", fontsize=14)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


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
