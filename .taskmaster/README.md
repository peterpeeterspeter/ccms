# TaskMaster Setup for LangChain Casino CMS

This directory contains the TaskMaster integration for your LangChain-native casino CMS project. TaskMaster provides structured task management that integrates seamlessly with Claude Code workflows.

## Quick Start

1. **Initialize TaskMaster**
   ```bash
   python .taskmaster/taskmaster.py init
   ```

2. **Create your first task**
   ```bash
   python .taskmaster/taskmaster.py create \
     --title "Set up casino review chain" \
     --description "Implement LCEL chain for automated casino reviews" \
     --priority "high"
   ```

3. **Check what to work on next**
   ```bash
   python .taskmaster/taskmaster.py next
   ```

## Directory Structure

```
.taskmaster/
├── README.md              # This file
├── config.json           # TaskMaster configuration  
├── taskmaster.json       # Project metadata and task index
├── taskmaster.py         # CLI script for task management
├── tasks/               # Individual task JSON files
│   ├── task-001.json
│   └── task-002.json
└── templates/           # Templates for PRDs and tasks
    ├── prd-template.md
    └── task-template.json
```

## Configuration

The `config.json` file is configured for Claude Code with:
- **Provider**: `claude-code` (no API key needed)
- **Model**: `sonnet` (SWE score: 0.727)
- **System Prompt**: Customized for LangChain-native development
- **Allowed Tools**: Git, pytest, ruff, mypy, npm, poetry, uv
- **Standards**: LCEL-first, Pydantic v2, compliance gates

## Claude Code Integration

TaskMaster is designed to work with your project's `CLAUDE.md` guidelines:

### Core Principles Alignment
- **LangChain-Native Only**: LCEL + LangGraph, no ad-hoc HTTP
- **Deterministic Contracts**: Pydantic v2 models for all I/O
- **Agent-First, Bounded**: Narrow agents with LangGraph checkpointing
- **Multitenant by Design**: All runs parameterized by `tenant_id`
- **Auditability**: LangSmith tracing and versioned prompts

### Task Categories
- `development`: Core feature implementation
- `testing`: Unit tests and golden evaluations
- `compliance`: QA gates and compliance checking
- `documentation`: Schema migrations and architecture docs
- `integration`: Tool adapters and external service connections

## Using with Claude Code

### Slash Commands
Use `/taskmaster` in your Claude Code sessions to access TaskMaster functionality directly.

### Workflow Integration
1. **Planning Phase**: Create tasks from PRDs using the template
2. **Development Phase**: Update task status as you progress
3. **Completion Phase**: Mark tasks complete after validation

### Example Workflow
```bash
# Start with next priority task
python .taskmaster/taskmaster.py next

# Update status when you begin work
python .taskmaster/taskmaster.py set-status --id task-001 --status in-progress

# Add notes during development
python .taskmaster/taskmaster.py set-status --id task-001 --status in-progress \
  --notes "Implemented base LCEL chain, need to add error handling"

# Mark complete after tests pass
python .taskmaster/taskmaster.py set-status --id task-001 --status completed
```

## PRD-Driven Development

Use the PRD template in `templates/prd-template.md` to:
1. Define clear requirements and success criteria
2. Break down complex features into manageable tasks
3. Ensure alignment with LangChain-native architecture
4. Document compliance and testing requirements

## Task Schema

Each task includes:
- **Technical Specs**: Components, schemas, chains, tools
- **Testing Requirements**: Unit tests, golden evals, LangSmith traces
- **Compliance Checks**: QA gates, jurisdiction requirements
- **Deliverables**: Code files, documentation, migrations

## Status Tracking

Task statuses:
- `pending`: Ready to start
- `in-progress`: Currently being worked on
- `completed`: Finished and validated
- `blocked`: Waiting for dependencies
- `cancelled`: No longer needed

## Reporting

Generate project status reports:
```bash
python .taskmaster/taskmaster.py report
```

This provides:
- Completion percentages
- Task distribution by status
- Recent activity
- Next recommended task

## Best Practices

1. **Keep tasks atomic**: Each task should be completable in 1-4 hours
2. **Link dependencies**: Use task IDs to reference prerequisites
3. **Update frequently**: Change status as you progress
4. **Document blockers**: Note what's preventing task completion
5. **Follow DoD**: Complete Definition of Done checklist before marking complete

## Integration with Project Tools

TaskMaster works alongside your existing tools:
- **Git**: Commit messages can reference task IDs
- **LangSmith**: Traces can be tagged with task context
- **Testing**: pytest and evals run automatically
- **Linting**: ruff and mypy validation included
- **Compliance**: QA gates enforce project standards

This structured approach ensures your LangChain casino CMS development stays organized, traceable, and aligned with your project's high standards.