from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StepName(str, Enum):
    RESEARCH = "research"
    SCREENSHOT = "screenshot"
    CONTENT = "content"
    QA = "qa"
    PUBLISH = "publish"


class StepStatus(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    SKIPPED = "skipped"


class StepResult(BaseModel):
    name: StepName
    status: StepStatus
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # WARP.md structured logs: tenant_id, chain, node, duration_ms
    tenant_id: Optional[str] = None
    chain: str = "review_orchestrator"
    node: str = Field(..., description="Node identifier matching step name")

    details: Dict[str, object] = Field(default_factory=dict)
    error: Optional[str] = None
    logs: List[str] = Field(default_factory=list)

    def close(self) -> "StepResult":
        self.finished_at = datetime.utcnow()
        if self.started_at and self.finished_at:
            self.duration_ms = int((self.finished_at - self.started_at).total_seconds() * 1000)
        return self


class PipelineConfig(BaseModel):
    enable_research: bool = True
    enable_screenshot: bool = False
    enable_content: bool = False
    enable_qa: bool = False
    enable_publish: bool = False

    # simple retry budget per step (can be expanded later)
    max_retries: int = 0


class OrchestrationState(BaseModel):
    tenant_id: str
    brand: str
    locale: str = "en-US"
    query: Optional[str] = None

    steps: Dict[StepName, StepResult] = Field(default_factory=dict)
    last_step: Optional[StepName] = None

    # convenience accessor
    def add_result(self, result: StepResult) -> None:
        self.steps[result.name] = result
        self.last_step = result.name
