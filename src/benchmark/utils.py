import platform
import time
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import psutil


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
        mongodb_mem: List[float]
):
    metrics = [
        ('CPU Usage (%)', cpu_usage, 'blue'),
        ('System Memory Usage (%)', memory_usage, 'green'),
        ('Wall Latency (ms)', wall_latency_ms, 'red'),
        ('Driver Latency (ms)', driver_latency_ms, 'orange'),
    ]

    if mongodb_mem:
        metrics.append(('MongoDB Memory (MB)', mongodb_mem, 'purple'))

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
