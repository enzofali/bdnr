from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BenchmarkResult:
    summary: Dict[str, float]
    series: Dict[str, List[float]]
