"""Data models for InvariantBench."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any


class TestStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


@dataclass
class TestCaseResult:
    name: str
    status: TestStatus
    duration_ms: float
    message: Optional[str] = None
    stack_trace: Optional[str] = None


@dataclass
class TaskMetadata:
    task_id: str
    title: str
    domain: str
    difficulty: str  # "Hard" or "Expert"
    failure_mode: str
    invariant_guarantee: str
    targeted_llms: List[str]


@dataclass
class TaskEvaluationResult:
    task_id: str
    title: str
    domain: str
    target_evaluated: str  # e.g., "ground_truth", "buggy_llm_baseline", "custom"
    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    duration_ms: float
    test_cases: List[TestCaseResult] = field(default_factory=list)
    failure_summary: Optional[str] = None


@dataclass
class BenchmarkSummary:
    timestamp: str
    target_evaluated: str
    total_tasks: int
    passed_tasks: int
    failed_tasks: int
    pass_rate_pct: float
    total_duration_sec: float
    domain_scores: Dict[str, Dict[str, Any]]
    results: List[TaskEvaluationResult]
