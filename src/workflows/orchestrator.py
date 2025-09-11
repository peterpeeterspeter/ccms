from __future__ import annotations

import logging
from typing import Dict, List, Literal, Optional

from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from ..schemas.pipeline import (
    OrchestrationState,
    PipelineConfig,
    StepName,
    StepResult,
    StepStatus,
)


class ReviewOrchestrator:
    """WARP-compliant LangGraph orchestrator for casino reviews.

    Schema-first, feature-flag gated, with LCEL components for each step.
    Supports incremental testing: when a step passes its gate, it's included
    in the workflow and not redundantly retested.
    """

    def __init__(self, config: PipelineConfig, tenant_id: str = "crashcasino"):
        self.config = config
        self.tenant_id = tenant_id
        self.logger = logging.getLogger(__name__)
        self._workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with feature-flag gated nodes."""
        workflow = StateGraph(OrchestrationState)

        # Add nodes based on feature flags
        if self.config.enable_research:
            workflow.add_node("research", self._research_step)

        if self.config.enable_screenshot:
            workflow.add_node("screenshot", self._screenshot_step)

        if self.config.enable_content:
            workflow.add_node("content", self._content_step)

        if self.config.enable_qa:
            workflow.add_node("qa", self._qa_step)

        if self.config.enable_publish:
            workflow.add_node("publish", self._publish_step)

        # Build edges based on enabled steps
        self._add_conditional_edges(workflow)

        # Set entry point
        if self.config.enable_research:
            workflow.set_entry_point("research")
        elif self.config.enable_screenshot:
            workflow.set_entry_point("screenshot")
        elif self.config.enable_content:
            workflow.set_entry_point("content")
        elif self.config.enable_qa:
            workflow.set_entry_point("qa")
        elif self.config.enable_publish:
            workflow.set_entry_point("publish")
        else:
            # No steps enabled - add a dummy node
            workflow.add_node("noop", self._noop_step)
            workflow.set_entry_point("noop")

        return workflow

    def _add_conditional_edges(self, workflow: StateGraph) -> None:
        """Add edges between enabled steps in order."""
        enabled_steps = []
        if self.config.enable_research:
            enabled_steps.append("research")
        if self.config.enable_screenshot:
            enabled_steps.append("screenshot")
        if self.config.enable_content:
            enabled_steps.append("content")
        if self.config.enable_qa:
            enabled_steps.append("qa")
        if self.config.enable_publish:
            enabled_steps.append("publish")

        # Chain the steps together
        for i in range(len(enabled_steps) - 1):
            current_step = enabled_steps[i]
            next_step = enabled_steps[i + 1]
            workflow.add_edge(current_step, next_step)

        # Last step goes to END
        if enabled_steps:
            workflow.add_edge(enabled_steps[-1], END)
        else:
            workflow.add_edge("noop", END)

    def _research_step(self, state: OrchestrationState) -> OrchestrationState:
        """Research step - placeholder for real research agent."""
        result = StepResult(
            name=StepName.RESEARCH,
            status=StepStatus.SUCCESS,
            tenant_id=self.tenant_id,
            node="research",
            logs=[f"Research completed for brand: {state.brand}"]
        ).close()

        state.add_result(result)
        self.logger.info(
            f"Research step completed - tenant: {self.tenant_id}, "
            f"brand: {state.brand}, duration: {result.duration_ms}ms"
        )
        return state

    def _screenshot_step(self, state: OrchestrationState) -> OrchestrationState:
        """Screenshot step - placeholder for intelligent screenshot system."""
        result = StepResult(
            name=StepName.SCREENSHOT,
            status=StepStatus.SUCCESS,
            tenant_id=self.tenant_id,
            node="screenshot",
            logs=[f"Screenshots captured for brand: {state.brand}"]
        ).close()

        state.add_result(result)
        self.logger.info(
            f"Screenshot step completed - tenant: {self.tenant_id}, "
            f"brand: {state.brand}, duration: {result.duration_ms}ms"
        )
        return state

    def _content_step(self, state: OrchestrationState) -> OrchestrationState:
        """Content generation step - placeholder for content agent."""
        result = StepResult(
            name=StepName.CONTENT,
            status=StepStatus.SUCCESS,
            tenant_id=self.tenant_id,
            node="content",
            logs=[f"Content generated for brand: {state.brand}"]
        ).close()

        state.add_result(result)
        self.logger.info(
            f"Content step completed - tenant: {self.tenant_id}, "
            f"brand: {state.brand}, duration: {result.duration_ms}ms"
        )
        return state

    def _qa_step(self, state: OrchestrationState) -> OrchestrationState:
        """QA validation step - placeholder for QA agent."""
        result = StepResult(
            name=StepName.QA,
            status=StepStatus.SUCCESS,
            tenant_id=self.tenant_id,
            node="qa",
            logs=[f"QA validation passed for brand: {state.brand}"]
        ).close()

        state.add_result(result)
        self.logger.info(
            f"QA step completed - tenant: {self.tenant_id}, "
            f"brand: {state.brand}, duration: {result.duration_ms}ms"
        )
        return state

    def _publish_step(self, state: OrchestrationState) -> OrchestrationState:
        """Publishing step - placeholder for WordPress publishing."""
        result = StepResult(
            name=StepName.PUBLISH,
            status=StepStatus.SUCCESS,
            tenant_id=self.tenant_id,
            node="publish",
            logs=[f"Review published for brand: {state.brand}"]
        ).close()

        state.add_result(result)
        self.logger.info(
            f"Publish step completed - tenant: {self.tenant_id}, "
            f"brand: {state.brand}, duration: {result.duration_ms}ms"
        )
        return state

    def _noop_step(self, state: OrchestrationState) -> OrchestrationState:
        """No-op step when no other steps are enabled."""
        result = StepResult(
            name=StepName.RESEARCH,  # Arbitrary assignment
            status=StepStatus.SKIPPED,
            tenant_id=self.tenant_id,
            node="noop",
            logs=["No steps enabled, workflow completed"]
        ).close()

        state.add_result(result)
        self.logger.info("No-op step - no workflow steps enabled")
        return state

    def compile(self) -> StateGraph:
        """Compile the workflow for execution."""
        return self._workflow.compile(checkpointer=MemorySaver())

    def run(self, brand: str, locale: str = "en-US", query: Optional[str] = None) -> OrchestrationState:
        """Run the orchestrated workflow."""
        initial_state = OrchestrationState(
            tenant_id=self.tenant_id,
            brand=brand,
            locale=locale,
            query=query
        )

        compiled_workflow = self.compile()
        result = compiled_workflow.invoke(initial_state)

        return result
