"""
Task Decomposition Tool for OpenManus.

This tool provides capabilities to break complex tasks into smaller subtasks:
- Analyze complex tasks and identify component parts
- Structure subtasks with dependencies and priorities
- Track execution status and progress
- Support for parallel and sequential execution patterns
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from datetime import datetime
import uuid

# Import config system
from src.config import load_config, Config

# Configure logging
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Enum for task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Enum for task priority values."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1

class TaskDecompositionTool:
    """
    Tool for breaking complex tasks into manageable subtasks and tracking execution.
    Provides capabilities for dependency management, priority-based execution,
    and progress tracking.
    """
    
    def __init__(self, 
                storage_path: str = None,
                enable_notifications: bool = None,
                config_obj: Config = None):
        """
        Initialize the task decomposition tool.
        
        Args:
            storage_path: Path for storing task data (overrides config)
            enable_notifications: Whether to enable notifications for task status changes (overrides config)
            config_obj: Config object for configuration
        """
        # Load configuration
        if config_obj is None:
            config_obj = load_config()
            
        # Get configuration or use defaults
        if storage_path is None:
            storage_path = config_obj.get_tool_config(
                "task_decomposition", 
                "storage_path", 
                os.environ.get("OPENMANUS_TASK_STORAGE_PATH", "data/tasks")
            )
            
        if enable_notifications is None:
            enable_notifications = config_obj.get_tool_config(
                "task_decomposition", 
                "enable_notifications", 
                os.environ.get("OPENMANUS_TASK_NOTIFICATIONS", "0").lower() in ("1", "true", "yes")
            )
        
        self.storage_path = os.path.abspath(storage_path)
        self.enable_notifications = enable_notifications
        self.tasks = {}  # In-memory cache of tasks
        self.task_graphs = {}  # Stores task dependency relationships
        
        # Ensure storage directory exists
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load existing tasks if any
        self._load_tasks()
    
    def _load_tasks(self) -> None:
        """Load existing tasks from storage."""
        try:
            tasks_file = os.path.join(self.storage_path, "tasks.json")
            if os.path.exists(tasks_file):
                with open(tasks_file, 'r') as f:
                    self.tasks = json.load(f)
                logger.info(f"Loaded {len(self.tasks)} tasks from storage")
            
            # Load task graphs
            graphs_file = os.path.join(self.storage_path, "task_graphs.json")
            if os.path.exists(graphs_file):
                with open(graphs_file, 'r') as f:
                    self.task_graphs = json.load(f)
                logger.info(f"Loaded {len(self.task_graphs)} task graphs from storage")
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            # Initialize empty if load fails
            self.tasks = {}
            self.task_graphs = {}
    
    def _save_tasks(self) -> bool:
        """Save tasks to storage."""
        try:
            # Ensure directory exists
            os.makedirs(self.storage_path, exist_ok=True)
            
            # Save tasks
            tasks_file = os.path.join(self.storage_path, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(self.tasks, f, indent=2)
            
            # Save task graphs
            graphs_file = os.path.join(self.storage_path, "task_graphs.json")
            with open(graphs_file, 'w') as f:
                json.dump(self.task_graphs, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
            return False
    
    def create_task(self, 
                   title: str, 
                   description: str, 
                   priority: Union[str, int] = "MEDIUM",
                   parent_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new task or subtask.
        
        Args:
            title: Task title
            description: Task description
            priority: Task priority (can be string name or int value)
            parent_id: Optional ID of parent task
            metadata: Optional additional task metadata
            
        Returns:
            Created task object
        """
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Parse priority
        if isinstance(priority, str):
            try:
                priority = TaskPriority[priority.upper()].value
            except KeyError:
                priority = TaskPriority.MEDIUM.value
        
        # Create timestamp
        timestamp = datetime.now().isoformat()
        
        # Create task object
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "status": TaskStatus.PENDING.value,
            "priority": priority,
            "created_at": timestamp,
            "updated_at": timestamp,
            "completed_at": None,
            "parent_id": parent_id,
            "dependencies": [],
            "blockers": [],
            "metadata": metadata or {},
            "progress": 0,
            "estimated_effort": None,
            "actual_effort": None,
            "assignee": None,
            "notes": []
        }
        
        # Store task
        self.tasks[task_id] = task
        
        # Update dependency graph
        if parent_id:
            if parent_id not in self.task_graphs:
                self.task_graphs[parent_id] = {"children": [], "dependencies": []}
            
            if task_id not in self.task_graphs[parent_id]["children"]:
                self.task_graphs[parent_id]["children"].append(task_id)
        
        # Initialize this task's graph entry
        self.task_graphs[task_id] = {"children": [], "dependencies": []}
        
        # Save to storage
        self._save_tasks()
        
        return task
    
    def add_dependency(self, task_id: str, depends_on_id: str) -> bool:
        """
        Add a dependency between tasks.
        
        Args:
            task_id: ID of the dependent task
            depends_on_id: ID of the task it depends on
            
        Returns:
            True if successful, False otherwise
        """
        # Verify both tasks exist
        if task_id not in self.tasks or depends_on_id not in self.tasks:
            logger.error(f"Cannot add dependency: one or both tasks do not exist")
            return False
        
        # Prevent circular dependencies
        if self._would_create_cycle(task_id, depends_on_id):
            logger.error(f"Cannot add dependency: would create circular dependency")
            return False
        
        # Add dependency
        if depends_on_id not in self.tasks[task_id]["dependencies"]:
            self.tasks[task_id]["dependencies"].append(depends_on_id)
        
        # Add as blocker if depends_on is not completed
        if self.tasks[depends_on_id]["status"] != TaskStatus.COMPLETED.value:
            if depends_on_id not in self.tasks[task_id]["blockers"]:
                self.tasks[task_id]["blockers"].append(depends_on_id)
            
            # Update status to blocked if currently pending
            if self.tasks[task_id]["status"] == TaskStatus.PENDING.value:
                self.tasks[task_id]["status"] = TaskStatus.BLOCKED.value
        
        # Update task graph
        if task_id not in self.task_graphs:
            self.task_graphs[task_id] = {"children": [], "dependencies": []}
        
        if depends_on_id not in self.task_graphs[task_id]["dependencies"]:
            self.task_graphs[task_id]["dependencies"].append(depends_on_id)
        
        # Save changes
        self._save_tasks()
        
        return True
    
    def _would_create_cycle(self, task_id: str, depends_on_id: str) -> bool:
        """
        Check if adding a dependency would create a circular reference.
        
        Args:
            task_id: ID of the dependent task
            depends_on_id: ID of the task it depends on
            
        Returns:
            True if circular dependency would be created, False otherwise
        """
        # If both IDs are the same, it's a cycle
        if task_id == depends_on_id:
            return True
        
        # Check if depends_on_id already depends on task_id (directly or indirectly)
        visited = set()
        
        def dfs_check_cycle(current_id):
            if current_id == task_id:
                return True
            
            visited.add(current_id)
            
            # Check direct dependencies
            for dep_id in self.tasks.get(current_id, {}).get("dependencies", []):
                if dep_id not in visited:
                    if dfs_check_cycle(dep_id):
                        return True
            
            # Check parent relationship
            parent_id = self.tasks.get(current_id, {}).get("parent_id")
            if parent_id and parent_id not in visited:
                if dfs_check_cycle(parent_id):
                    return True
            
            return False
        
        return dfs_check_cycle(depends_on_id)
    
    def update_task_status(self, task_id: str, status: str, progress: Optional[int] = None) -> bool:
        """
        Update a task's status and optionally progress.
        
        Args:
            task_id: ID of the task to update
            status: New status value (use TaskStatus enum values)
            progress: Optional progress percentage (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
        
        # Validate status
        try:
            status_enum = TaskStatus(status)
        except ValueError:
            logger.error(f"Invalid status value: {status}")
            return False
        
        old_status = self.tasks[task_id]["status"]
        self.tasks[task_id]["status"] = status
        self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        # Set completion time if completing
        if status == TaskStatus.COMPLETED.value and old_status != TaskStatus.COMPLETED.value:
            self.tasks[task_id]["completed_at"] = datetime.now().isoformat()
            
            # Automatically set progress to 100% if completed
            self.tasks[task_id]["progress"] = 100
            
            # Update tasks that depend on this one
            self._update_dependent_tasks(task_id)
        
        # Update progress if provided
        if progress is not None:
            self.tasks[task_id]["progress"] = max(0, min(100, progress))
        
        # Save changes
        self._save_tasks()
        
        # Send notification if enabled
        if self.enable_notifications:
            self._send_status_notification(task_id, old_status, status)
        
        return True
    
    def _update_dependent_tasks(self, completed_task_id: str) -> None:
        """
        Update tasks that depend on a completed task.
        
        Args:
            completed_task_id: ID of the completed task
        """
        # Find all tasks that have this as a dependency
        for task_id, task in self.tasks.items():
            if completed_task_id in task.get("blockers", []):
                # Remove the completed task from blockers
                task["blockers"].remove(completed_task_id)
                
                # If no blockers remain and task is blocked, set it to pending
                if not task["blockers"] and task["status"] == TaskStatus.BLOCKED.value:
                    task["status"] = TaskStatus.PENDING.value
                    task["updated_at"] = datetime.now().isoformat()
                    
                    # Send notification if enabled
                    if self.enable_notifications:
                        self._send_status_notification(
                            task_id, 
                            TaskStatus.BLOCKED.value,
                            TaskStatus.PENDING.value
                        )
    
    def _send_status_notification(self, task_id: str, old_status: str, new_status: str) -> None:
        """
        Send notification about task status change.
        
        Args:
            task_id: ID of the task
            old_status: Previous status
            new_status: New status
        """
        # This is a placeholder for notification logic
        task = self.tasks[task_id]
        notification = {
            "task_id": task_id,
            "title": task["title"],
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log the notification (would send to appropriate channels in production)
        logger.info(f"Task Status Change: {json.dumps(notification)}")
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by ID.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task object or None if not found
        """
        return self.tasks.get(task_id)
    
    def get_subtasks(self, parent_id: str) -> List[Dict[str, Any]]:
        """
        Get all subtasks of a task.
        
        Args:
            parent_id: ID of the parent task
            
        Returns:
            List of subtask objects
        """
        return [
            task for task_id, task in self.tasks.items()
            if task.get("parent_id") == parent_id
        ]
    
    def delete_task(self, task_id: str, cascade: bool = False) -> bool:
        """
        Delete a task and optionally its subtasks.
        
        Args:
            task_id: ID of the task to delete
            cascade: Whether to also delete subtasks
            
        Returns:
            True if successful, False otherwise
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
        
        # If cascade is True, delete all subtasks
        if cascade:
            subtasks = self.get_subtasks(task_id)
            for subtask in subtasks:
                self.delete_task(subtask["id"], cascade=True)
        
        # Remove from parent's children list if it has a parent
        parent_id = self.tasks[task_id].get("parent_id")
        if parent_id and parent_id in self.task_graphs:
            if task_id in self.task_graphs[parent_id]["children"]:
                self.task_graphs[parent_id]["children"].remove(task_id)
        
        # Remove from any task's dependencies and blockers
        for other_id, other_task in self.tasks.items():
            if task_id in other_task.get("dependencies", []):
                other_task["dependencies"].remove(task_id)
            if task_id in other_task.get("blockers", []):
                other_task["blockers"].remove(task_id)
        
        # Remove from task graph entries
        if task_id in self.task_graphs:
            del self.task_graphs[task_id]
        
        # Remove from task dictionary
        del self.tasks[task_id]
        
        # Save changes
        self._save_tasks()
        
        return True
    
    def get_next_tasks(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get the next tasks to work on based on priority and blockers.
        
        Args:
            count: Number of tasks to return
            
        Returns:
            List of task objects sorted by priority
        """
        # Get tasks that are ready to work on (PENDING status, no blockers)
        available_tasks = [
            task for task_id, task in self.tasks.items()
            if task["status"] == TaskStatus.PENDING.value and not task["blockers"]
        ]
        
        # Sort by priority (higher value means higher priority)
        available_tasks.sort(key=lambda t: t["priority"], reverse=True)
        
        # Return the requested number of tasks
        return available_tasks[:count]
    
    def get_critical_path(self, root_task_id: str) -> List[Dict[str, Any]]:
        """
        Get the critical path for a task graph.
        
        Args:
            root_task_id: ID of the root task
            
        Returns:
            List of tasks in the critical path
        """
        if root_task_id not in self.tasks:
            logger.error(f"Task {root_task_id} not found")
            return []
        
        # Calculate earliest completion time for each task
        earliest_completion = {}
        
        def calculate_earliest_completion(task_id):
            if task_id in earliest_completion:
                return earliest_completion[task_id]
            
            task = self.tasks.get(task_id)
            if not task:
                return 0
            
            # Estimate task duration (simplified)
            duration = task.get("estimated_effort", 1)
            
            # Calculate earliest completion from dependencies
            deps_completion = 0
            for dep_id in task.get("dependencies", []):
                deps_completion = max(deps_completion, calculate_earliest_completion(dep_id))
            
            # Earliest completion is dependencies plus own duration
            earliest_completion[task_id] = deps_completion + duration
            return earliest_completion[task_id]
        
        # Calculate for all tasks starting from root
        calculate_earliest_completion(root_task_id)
        
        # Find the critical path
        critical_path = []
        current_id = root_task_id
        
        while current_id:
            task = self.tasks.get(current_id)
            if not task:
                break
                
            critical_path.append(task)
            
            # Find the dependency with the latest earliest completion
            next_id = None
            max_completion = -1
            
            for dep_id in task.get("dependencies", []):
                if dep_id in earliest_completion and earliest_completion[dep_id] > max_completion:
                    max_completion = earliest_completion[dep_id]
                    next_id = dep_id
            
            current_id = next_id
        
        return critical_path
    
    def decompose_task(self, 
                      task_id: str, 
                      subtasks: List[Dict[str, Any]],
                      auto_link: bool = True) -> List[str]:
        """
        Decompose a task into subtasks.
        
        Args:
            task_id: ID of the parent task
            subtasks: List of subtask definitions (each with title, description, etc.)
            auto_link: Whether to automatically link sequential subtasks
            
        Returns:
            List of created subtask IDs
        """
        if task_id not in self.tasks:
            logger.error(f"Parent task {task_id} not found")
            return []
        
        created_ids = []
        prev_id = None
        
        # Create each subtask
        for subtask_def in subtasks:
            # Extract fields with defaults
            title = subtask_def.get("title", "Unnamed Subtask")
            description = subtask_def.get("description", "")
            priority = subtask_def.get("priority", TaskPriority.MEDIUM.value)
            metadata = subtask_def.get("metadata", {})
            
            # Create the subtask
            subtask = self.create_task(
                title=title,
                description=description,
                priority=priority,
                parent_id=task_id,
                metadata=metadata
            )
            
            subtask_id = subtask["id"]
            created_ids.append(subtask_id)
            
            # If specified, link to previous subtask
            if auto_link and prev_id:
                self.add_dependency(subtask_id, prev_id)
            
            # Update for next iteration
            prev_id = subtask_id
        
        # Update parent task
        parent_task = self.tasks[task_id]
        parent_task["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        self._save_tasks()
        
        return created_ids
    
    def get_all_tasks(self, 
                     status_filter: Optional[str] = None,
                     priority_filter: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all tasks, optionally filtered by status or priority.
        
        Args:
            status_filter: Optional status to filter by
            priority_filter: Optional priority to filter by
            
        Returns:
            List of task objects
        """
        tasks = list(self.tasks.values())
        
        # Apply status filter if provided
        if status_filter:
            tasks = [t for t in tasks if t["status"] == status_filter]
        
        # Apply priority filter if provided
        if priority_filter:
            tasks = [t for t in tasks if t["priority"] == priority_filter]
        
        return tasks
    
    def get_task_tree(self, root_task_id: str) -> Dict[str, Any]:
        """
        Get a hierarchical representation of a task and all its subtasks.
        
        Args:
            root_task_id: ID of the root task
            
        Returns:
            Task tree object
        """
        if root_task_id not in self.tasks:
            logger.error(f"Root task {root_task_id} not found")
            return {}
        
        # Build tree recursively
        def build_tree(task_id):
            task = self.tasks.get(task_id, {}).copy()
            
            # Find immediate children
            children = self.get_subtasks(task_id)
            
            # Build subtrees
            subtrees = [build_tree(child["id"]) for child in children]
            
            # Add children to task object
            task["children"] = subtrees
            
            return task
        
        return build_tree(root_task_id)
    
    def add_task_note(self, task_id: str, note: str) -> bool:
        """
        Add a note to a task.
        
        Args:
            task_id: ID of the task
            note: Note text
            
        Returns:
            True if successful, False otherwise
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
        
        # Create note object
        note_obj = {
            "text": note,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to task notes
        self.tasks[task_id]["notes"].append(note_obj)
        self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        self._save_tasks()
        
        return True
    
    def get_blocked_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks that are currently blocked.
        
        Returns:
            List of blocked task objects
        """
        return [
            task for task_id, task in self.tasks.items()
            if task["status"] == TaskStatus.BLOCKED.value
        ]
    
    def assign_task(self, task_id: str, assignee: str) -> bool:
        """
        Assign a task to someone.
        
        Args:
            task_id: ID of the task
            assignee: Name or ID of the assignee
            
        Returns:
            True if successful, False otherwise
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
        
        self.tasks[task_id]["assignee"] = assignee
        self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        self._save_tasks()
        
        return True
    
    def update_task_effort(self, 
                          task_id: str, 
                          estimated_effort: Optional[float] = None,
                          actual_effort: Optional[float] = None) -> bool:
        """
        Update effort estimates for a task.
        
        Args:
            task_id: ID of the task
            estimated_effort: Optional estimated effort value
            actual_effort: Optional actual effort value
            
        Returns:
            True if successful, False otherwise
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
        
        if estimated_effort is not None:
            self.tasks[task_id]["estimated_effort"] = estimated_effort
            
        if actual_effort is not None:
            self.tasks[task_id]["actual_effort"] = actual_effort
            
        self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        self._save_tasks()
        
        return True
    
    def get_task_dependencies(self, task_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get dependencies for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Dictionary with upstream and downstream dependencies
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return {"upstream": [], "downstream": []}
        
        # Get upstream dependencies (tasks this depends on)
        upstream_ids = self.tasks[task_id].get("dependencies", [])
        upstream = [self.tasks[dep_id] for dep_id in upstream_ids if dep_id in self.tasks]
        
        # Get downstream dependencies (tasks that depend on this)
        downstream = []
        for other_id, other_task in self.tasks.items():
            if task_id in other_task.get("dependencies", []):
                downstream.append(other_task)
        
        return {
            "upstream": upstream,
            "downstream": downstream
        }
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of all tasks.
        
        Returns:
            Summary report object
        """
        total_tasks = len(self.tasks)
        
        # Count tasks by status
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = 0
            
        for task in self.tasks.values():
            status = task["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate overall progress
        completed_count = status_counts.get(TaskStatus.COMPLETED.value, 0)
        overall_progress = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        # Get high priority tasks that are not completed
        high_priority_pending = [
            task for task in self.tasks.values()
            if task["priority"] >= TaskPriority.HIGH.value and task["status"] != TaskStatus.COMPLETED.value
        ]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_tasks": total_tasks,
            "status_breakdown": status_counts,
            "overall_progress": overall_progress,
            "high_priority_pending_count": len(high_priority_pending),
            "blocked_tasks_count": len(self.get_blocked_tasks()),
            "ready_tasks_count": len(self.get_next_tasks(count=1000))
        }