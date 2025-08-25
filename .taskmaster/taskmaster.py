#!/usr/bin/env python3
"""
TaskMaster Integration Script for LangChain Casino CMS
Provides task management functionality aligned with Claude Code workflows
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import argparse


@dataclass
class Task:
    """Task data structure"""
    id: str
    title: str
    description: str
    status: str
    priority: str
    category: str
    created_at: str
    updated_at: str
    estimated_hours: int = 0
    actual_hours: int = 0
    due_date: Optional[str] = None
    assignee: Optional[str] = None
    tags: List[str] = None
    dependencies: List[str] = None
    blockers: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.dependencies is None:
            self.dependencies = []
        if self.blockers is None:
            self.blockers = []


class TaskMaster:
    """TaskMaster integration for LangChain project"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.taskmaster_dir = self.project_root / ".taskmaster"
        self.config_file = self.taskmaster_dir / "config.json"
        self.taskmaster_file = self.taskmaster_dir / "taskmaster.json"
        self.tasks_dir = self.taskmaster_dir / "tasks"
        
        # Ensure directories exist
        self.taskmaster_dir.mkdir(exist_ok=True)
        self.tasks_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        self.taskmaster_data = self._load_taskmaster_data()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load TaskMaster configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_taskmaster_data(self) -> Dict[str, Any]:
        """Load main taskmaster data"""
        if self.taskmaster_file.exists():
            with open(self.taskmaster_file, 'r') as f:
                return json.load(f)
        
        # Default structure
        return {
            "version": "1.0.0",
            "projectId": "langchain-casino-cms",
            "initialized": True,
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "tasks": [],
            "currentTask": None,
            "metadata": {
                "totalTasks": 0,
                "completedTasks": 0,
                "inProgressTasks": 0,
                "pendingTasks": 0
            }
        }
    
    def _save_taskmaster_data(self):
        """Save taskmaster data to file"""
        self.taskmaster_data["lastUpdated"] = datetime.now(timezone.utc).isoformat()
        with open(self.taskmaster_file, 'w') as f:
            json.dump(self.taskmaster_data, f, indent=2)
    
    def _generate_task_id(self) -> str:
        """Generate next task ID"""
        task_count = len(self.taskmaster_data["tasks"]) + 1
        return f"task-{task_count:03d}"
    
    def create_task(self, title: str, description: str, priority: str = "medium", 
                   category: str = "development", **kwargs) -> Dict[str, Any]:
        """Create a new task"""
        task_id = self._generate_task_id()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        task_data = {
            "id": task_id,
            "title": title,
            "description": description,
            "status": "pending",
            "priority": priority,
            "category": category,
            "estimatedHours": kwargs.get("estimated_hours", 0),
            "actualHours": 0,
            "createdAt": timestamp,
            "updatedAt": timestamp,
            "dueDate": kwargs.get("due_date"),
            "assignee": kwargs.get("assignee"),
            "tags": kwargs.get("tags", []),
            "dependencies": kwargs.get("dependencies", []),
            "blockers": kwargs.get("blockers", []),
            "requirements": {
                "functional": kwargs.get("functional_requirements", []),
                "technical": kwargs.get("technical_requirements", []),
                "compliance": kwargs.get("compliance_requirements", [])
            },
            "acceptanceCriteria": kwargs.get("acceptance_criteria", []),
            "technicalSpecs": {
                "components": kwargs.get("components", []),
                "schemas": kwargs.get("schemas", []),
                "chains": kwargs.get("chains", []),
                "tools": kwargs.get("tools", [])
            },
            "testingRequirements": {
                "unitTests": kwargs.get("unit_tests", True),
                "integrationTests": kwargs.get("integration_tests", False),
                "goldenEvals": kwargs.get("golden_evals", True),
                "langsmithTraces": kwargs.get("langsmith_traces", True)
            },
            "deliverables": kwargs.get("deliverables", []),
            "notes": [],
            "history": [
                {
                    "timestamp": timestamp,
                    "action": "created",
                    "user": "taskmaster",
                    "details": "Task created"
                }
            ]
        }
        
        # Save individual task file
        task_file = self.tasks_dir / f"{task_id}.json"
        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=2)
        
        # Update main taskmaster data
        self.taskmaster_data["tasks"].append(task_id)
        self.taskmaster_data["metadata"]["totalTasks"] += 1
        self.taskmaster_data["metadata"]["pendingTasks"] += 1
        self._save_taskmaster_data()
        
        return task_data
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        task_file = self.tasks_dir / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, 'r') as f:
                return json.load(f)
        return None
    
    def list_tasks(self, status: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List tasks with optional filtering"""
        tasks = []
        for task_id in self.taskmaster_data["tasks"]:
            task = self.get_task(task_id)
            if task:
                if status and task["status"] != status:
                    continue
                if category and task["category"] != category:
                    continue
                tasks.append(task)
        return tasks
    
    def update_task_status(self, task_id: str, new_status: str, notes: Optional[str] = None) -> bool:
        """Update task status"""
        task = self.get_task(task_id)
        if not task:
            return False
        
        old_status = task["status"]
        task["status"] = new_status
        task["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # Add history entry
        task["history"].append({
            "timestamp": task["updatedAt"],
            "action": "status_change",
            "user": "taskmaster",
            "details": f"Status changed from {old_status} to {new_status}"
        })
        
        if notes:
            task["notes"].append({
                "timestamp": task["updatedAt"],
                "note": notes,
                "user": "taskmaster"
            })
        
        # Save updated task
        task_file = self.tasks_dir / f"{task_id}.json"
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
        
        # Update metadata
        self._update_task_metadata(old_status, new_status)
        self._save_taskmaster_data()
        
        return True
    
    def _update_task_metadata(self, old_status: str, new_status: str):
        """Update task count metadata"""
        metadata = self.taskmaster_data["metadata"]
        
        # Decrement old status count
        if old_status == "pending":
            metadata["pendingTasks"] = max(0, metadata["pendingTasks"] - 1)
        elif old_status == "in-progress":
            metadata["inProgressTasks"] = max(0, metadata["inProgressTasks"] - 1)
        elif old_status == "completed":
            metadata["completedTasks"] = max(0, metadata["completedTasks"] - 1)
        
        # Increment new status count
        if new_status == "pending":
            metadata["pendingTasks"] += 1
        elif new_status == "in-progress":
            metadata["inProgressTasks"] += 1
        elif new_status == "completed":
            metadata["completedTasks"] += 1
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the next task to work on (highest priority pending task)"""
        pending_tasks = self.list_tasks(status="pending")
        if not pending_tasks:
            return None
        
        # Sort by priority (critical > high > medium > low)
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        pending_tasks.sort(key=lambda t: priority_order.get(t["priority"], 0), reverse=True)
        
        return pending_tasks[0]
    
    def generate_status_report(self) -> Dict[str, Any]:
        """Generate a status report"""
        metadata = self.taskmaster_data["metadata"]
        
        return {
            "projectId": self.taskmaster_data["projectId"],
            "lastUpdated": self.taskmaster_data["lastUpdated"],
            "summary": {
                "total": metadata["totalTasks"],
                "completed": metadata["completedTasks"],
                "inProgress": metadata["inProgressTasks"], 
                "pending": metadata["pendingTasks"],
                "completionRate": round((metadata["completedTasks"] / max(1, metadata["totalTasks"])) * 100, 2)
            },
            "recentTasks": self.list_tasks()[-5:],  # Last 5 tasks
            "nextTask": self.get_next_task()
        }


def main():
    """CLI interface for TaskMaster"""
    parser = argparse.ArgumentParser(description="TaskMaster CLI for LangChain Casino CMS")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize TaskMaster in project")
    
    # Create task command
    create_parser = subparsers.add_parser("create", help="Create a new task")
    create_parser.add_argument("--title", required=True, help="Task title")
    create_parser.add_argument("--description", required=True, help="Task description")
    create_parser.add_argument("--priority", default="medium", choices=["low", "medium", "high", "critical"])
    create_parser.add_argument("--category", default="development", help="Task category")
    
    # List tasks command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--category", help="Filter by category")
    
    # Show task command
    show_parser = subparsers.add_parser("show", help="Show task details")
    show_parser.add_argument("task_id", help="Task ID to show")
    
    # Update status command
    status_parser = subparsers.add_parser("set-status", help="Update task status")
    status_parser.add_argument("--id", required=True, help="Task ID")
    status_parser.add_argument("--status", required=True, 
                              choices=["pending", "in-progress", "completed", "blocked", "cancelled"])
    status_parser.add_argument("--notes", help="Optional notes")
    
    # Next task command
    subparsers.add_parser("next", help="Get next task to work on")
    
    # Status report command
    subparsers.add_parser("report", help="Generate status report")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize TaskMaster
    tm = TaskMaster()
    
    if args.command == "init":
        print(f"TaskMaster initialized in {tm.taskmaster_dir}")
        
    elif args.command == "create":
        task = tm.create_task(
            title=args.title,
            description=args.description,
            priority=args.priority,
            category=args.category
        )
        print(f"Created task: {task['id']} - {task['title']}")
        
    elif args.command == "list":
        tasks = tm.list_tasks(status=args.status, category=args.category)
        if not tasks:
            print("No tasks found")
        else:
            for task in tasks:
                print(f"{task['id']}: {task['title']} [{task['status']}] ({task['priority']})")
                
    elif args.command == "show":
        task = tm.get_task(args.task_id)
        if task:
            print(json.dumps(task, indent=2))
        else:
            print(f"Task not found: {args.task_id}")
            
    elif args.command == "set-status":
        success = tm.update_task_status(args.id, args.status, args.notes)
        if success:
            print(f"Updated task {args.id} status to {args.status}")
        else:
            print(f"Failed to update task: {args.id}")
            
    elif args.command == "next":
        task = tm.get_next_task()
        if task:
            print(f"Next task: {task['id']} - {task['title']}")
            print(f"Priority: {task['priority']}")
            print(f"Description: {task['description']}")
        else:
            print("No pending tasks")
            
    elif args.command == "report":
        report = tm.generate_status_report()
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()