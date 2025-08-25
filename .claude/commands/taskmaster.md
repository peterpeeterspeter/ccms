# TaskMaster Commands

## Initialize TaskMaster
Create a new TaskMaster project or reinitialize existing one.

```bash
cd /Users/Peter/LANGCHAIN\ 1.2/langchain
python .taskmaster/taskmaster.py init
```

## Create Tasks from PRD
Parse a Product Requirements Document and generate tasks.

```bash
# Create a task manually
python .taskmaster/taskmaster.py create \
  --title "Implement Universal RAG Chain" \
  --description "Build LCEL-based universal RAG chain with multitenant support" \
  --priority "high" \
  --category "development"
```

## Task Management
```bash
# List all tasks
python .taskmaster/taskmaster.py list

# List by status
python .taskmaster/taskmaster.py list --status pending
python .taskmaster/taskmaster.py list --status in-progress

# Show specific task
python .taskmaster/taskmaster.py show task-001

# Update task status
python .taskmaster/taskmaster.py set-status --id task-001 --status in-progress --notes "Started implementation"

# Get next task
python .taskmaster/taskmaster.py next

# Generate status report
python .taskmaster/taskmaster.py report
```

## Integration with Claude Code
The TaskMaster system is configured to work with Claude Code's Sonnet model and follows your project's CLAUDE.md guidelines:

- LCEL-first development approach
- Pydantic v2 schemas with migrations
- Multitenant architecture support
- Compliance and QA gates
- LangSmith tracing and evaluations

Use these commands within Claude Code sessions to maintain structured task management throughout your development workflow.