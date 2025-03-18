#!/usr/bin/env python3
"""
Example script demonstrating the usage of the Task Decomposition Tool.

This script shows how to break down complex tasks into subtasks,
manage dependencies, track progress, and handle task workflows.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Task Decomposition Tool
from src.tools.task_decomposition import TaskDecompositionTool, TaskStatus, TaskPriority

def main():
    """Main function demonstrating Task Decomposition Tool usage."""
    print("Task Decomposition Tool Usage Example")
    print("=" * 50)
    
    # Initialize the tool
    print("\nInitializing Task Decomposition Tool...")
    task_tool = TaskDecompositionTool(
        storage_path="data/tasks_example",
        enable_notifications=True
    )
    
    # 1. Create a main task (project)
    print("\n1. Creating a Main Project Task")
    print("-" * 50)
    
    project = task_tool.create_task(
        title="Implement New User Authentication System",
        description="Design and implement a new authentication system with OAuth2, MFA, and role-based access control",
        priority="HIGH",
        metadata={"project_code": "AUTH-2023", "deadline": "2025-06-01"}
    )
    
    print(f"Created project task: {project['id']}")
    print(f"Title: {project['title']}")
    print(f"Priority: {project['priority']} ({TaskPriority(project['priority']).name})")
    print(f"Status: {project['status']} ({TaskStatus(project['status']).name})")
    
    # 2. Decompose into subtasks
    print("\n2. Decomposing into Subtasks")
    print("-" * 50)
    
    subtasks = [
        {
            "title": "Research OAuth2 Providers",
            "description": "Evaluate different OAuth2 providers and select the best option for our needs",
            "priority": TaskPriority.MEDIUM.value,
            "metadata": {"estimated_hours": 10}
        },
        {
            "title": "Design Authentication Flow",
            "description": "Create diagram and specs for the authentication flow including MFA",
            "priority": TaskPriority.HIGH.value,
            "metadata": {"estimated_hours": 15}
        },
        {
            "title": "Implement OAuth2 Integration",
            "description": "Integrate the selected OAuth2 provider with our system",
            "priority": TaskPriority.HIGH.value,
            "metadata": {"estimated_hours": 20}
        },
        {
            "title": "Implement MFA",
            "description": "Add multi-factor authentication support",
            "priority": TaskPriority.MEDIUM.value,
            "metadata": {"estimated_hours": 15}
        },
        {
            "title": "Implement Role-Based Access",
            "description": "Create role-based access control system",
            "priority": TaskPriority.HIGH.value,
            "metadata": {"estimated_hours": 25}
        },
        {
            "title": "Create Admin UI",
            "description": "Develop admin interface for managing users and roles",
            "priority": TaskPriority.MEDIUM.value,
            "metadata": {"estimated_hours": 30}
        },
        {
            "title": "Write Tests",
            "description": "Develop comprehensive test suite for the authentication system",
            "priority": TaskPriority.HIGH.value,
            "metadata": {"estimated_hours": 15}
        },
        {
            "title": "Documentation",
            "description": "Create user and developer documentation",
            "priority": TaskPriority.LOW.value,
            "metadata": {"estimated_hours": 10}
        }
    ]
    
    # Create all subtasks linked to the main task
    subtask_ids = task_tool.decompose_task(
        project["id"],
        subtasks,
        auto_link=False  # Don't automatically link them sequentially
    )
    
    print(f"Created {len(subtask_ids)} subtasks")
    
    # Get all subtasks to work with them
    all_subtasks = []
    for subtask_id in subtask_ids:
        subtask = task_tool.get_task(subtask_id)
        print(f"  - {subtask['title']} (ID: {subtask_id})")
        all_subtasks.append(subtask)
    
    # 3. Add dependencies between tasks
    print("\n3. Adding Task Dependencies")
    print("-" * 50)
    
    # Find tasks by title
    def find_task_by_title(title):
        for task in all_subtasks:
            if task["title"] == title:
                return task
        return None
    
    research = find_task_by_title("Research OAuth2 Providers")
    design = find_task_by_title("Design Authentication Flow")
    oauth = find_task_by_title("Implement OAuth2 Integration")
    mfa = find_task_by_title("Implement MFA")
    rbac = find_task_by_title("Implement Role-Based Access")
    admin_ui = find_task_by_title("Create Admin UI")
    tests = find_task_by_title("Write Tests")
    docs = find_task_by_title("Documentation")
    
    # Set up dependencies
    dependencies = [
        # Design depends on Research
        (design["id"], research["id"]),
        # OAuth implementation depends on Design and Research
        (oauth["id"], design["id"]),
        (oauth["id"], research["id"]),
        # MFA depends on OAuth
        (mfa["id"], oauth["id"]),
        # RBAC depends on OAuth
        (rbac["id"], oauth["id"]),
        # Admin UI depends on RBAC
        (admin_ui["id"], rbac["id"]),
        # Tests depend on all implementations
        (tests["id"], oauth["id"]),
        (tests["id"], mfa["id"]),
        (tests["id"], rbac["id"]),
        (tests["id"], admin_ui["id"]),
        # Documentation depends on all implementations
        (docs["id"], oauth["id"]),
        (docs["id"], mfa["id"]),
        (docs["id"], rbac["id"]),
        (docs["id"], admin_ui["id"])
    ]
    
    for dep_task_id, depends_on_id in dependencies:
        success = task_tool.add_dependency(dep_task_id, depends_on_id)
        if success:
            dep_task = task_tool.get_task(dep_task_id)
            depends_on = task_tool.get_task(depends_on_id)
            print(f"Added dependency: '{dep_task['title']}' depends on '{depends_on['title']}'")
        else:
            print(f"Failed to add dependency between {dep_task_id} and {depends_on_id}")
    
    # 4. Get next tasks to work on
    print("\n4. Getting Next Tasks to Work On")
    print("-" * 50)
    
    next_tasks = task_tool.get_next_tasks(count=3)
    print(f"Found {len(next_tasks)} available tasks to work on:")
    
    for i, task in enumerate(next_tasks):
        print(f"  {i+1}. {task['title']} (Priority: {TaskPriority(task['priority']).name})")
    
    # 5. Update task status
    print("\n5. Updating Task Status")
    print("-" * 50)
    
    # Mark research as completed
    research_update = task_tool.update_task_status(
        research["id"],
        TaskStatus.COMPLETED.value,
        progress=100
    )
    
    print(f"Updated Research task status to COMPLETED: {research_update}")
    
    # Start working on design
    design_update = task_tool.update_task_status(
        design["id"],
        TaskStatus.IN_PROGRESS.value,
        progress=25
    )
    
    print(f"Updated Design task status to IN_PROGRESS (25%): {design_update}")
    
    # Check next tasks again
    print("\nUpdated next tasks after status changes:")
    next_tasks = task_tool.get_next_tasks(count=3)
    for i, task in enumerate(next_tasks):
        print(f"  {i+1}. {task['title']} (Priority: {TaskPriority(task['priority']).name})")
    
    # 6. Get blocked tasks
    print("\n6. Viewing Blocked Tasks")
    print("-" * 50)
    
    blocked_tasks = task_tool.get_blocked_tasks()
    print(f"Found {len(blocked_tasks)} blocked tasks:")
    
    for i, task in enumerate(blocked_tasks):
        blockers = [task_tool.get_task(blocker_id)["title"] for blocker_id in task["blockers"]]
        print(f"  {i+1}. {task['title']} - Blocked by: {', '.join(blockers)}")
    
    # 7. Assign tasks to team members
    print("\n7. Assigning Tasks")
    print("-" * 50)
    
    # Assign design task
    task_tool.assign_task(design["id"], "Alice")
    print(f"Assigned '{design['title']}' to Alice")
    
    # Assign research completion review
    task_tool.assign_task(research["id"], "Bob")
    print(f"Assigned '{research['title']}' review to Bob")
    
    # 8. Add task notes
    print("\n8. Adding Task Notes")
    print("-" * 50)
    
    research_note = task_tool.add_task_note(
        research["id"],
        "After researching options, recommend using Auth0 for our OAuth2 provider."
    )
    
    design_note = task_tool.add_task_note(
        design["id"],
        "Started creating sequence diagrams for the auth flow. Will review with security team tomorrow."
    )
    
    print(f"Added notes to tasks: {research_note}, {design_note}")
    
    # Display task with notes
    research_with_notes = task_tool.get_task(research["id"])
    print(f"\nTask: {research_with_notes['title']}")
    print(f"Status: {TaskStatus(research_with_notes['status']).name}")
    print(f"Assignee: {research_with_notes['assignee']}")
    
    print("Notes:")
    for note in research_with_notes["notes"]:
        note_time = datetime.fromisoformat(note["timestamp"]).strftime("%Y-%m-%d %H:%M")
        print(f"  [{note_time}] {note['text']}")
    
    # 9. Update estimated and actual effort
    print("\n9. Updating Task Effort")
    print("-" * 50)
    
    task_tool.update_task_effort(
        research["id"],
        estimated_effort=10,
        actual_effort=12
    )
    
    task_tool.update_task_effort(
        design["id"],
        estimated_effort=15
    )
    
    research_updated = task_tool.get_task(research["id"])
    print(f"Task: {research_updated['title']}")
    print(f"Estimated effort: {research_updated['estimated_effort']} hours")
    print(f"Actual effort: {research_updated['actual_effort']} hours")
    
    # 10. Complete design task and see effect on dependencies
    print("\n10. Completing Tasks and Updating Dependencies")
    print("-" * 50)
    
    # Complete design task
    task_tool.update_task_status(
        design["id"],
        TaskStatus.COMPLETED.value,
        progress=100
    )
    
    print(f"Completed '{design['title']}' task")
    
    # Check if OAuth implementation is now unblocked
    oauth_updated = task_tool.get_task(oauth["id"])
    print(f"Task: {oauth_updated['title']}")
    print(f"Status: {TaskStatus(oauth_updated['status']).name}")
    print(f"Blockers: {len(oauth_updated['blockers'])}")
    
    if not oauth_updated["blockers"]:
        print("The OAuth Integration task is now unblocked!")
    else:
        blockers = [task_tool.get_task(blocker_id)["title"] for blocker_id in oauth_updated["blockers"]]
        print(f"The OAuth Integration task is still blocked by: {', '.join(blockers)}")
    
    # 11. View task tree
    print("\n11. Viewing Task Tree")
    print("-" * 50)
    
    task_tree = task_tool.get_task_tree(project["id"])
    
    print(f"Task Tree for: {task_tree['title']}")
    print(f"Status: {TaskStatus(task_tree['status']).name}")
    print(f"Subtasks: {len(task_tree['children'])}")
    
    # Print a simple tree visualization
    print("\nProject Structure:")
    print(f"└── {task_tree['title']}")
    
    for child in task_tree['children']:
        status_emoji = "✅" if child['status'] == TaskStatus.COMPLETED.value else "⏳" if child['status'] == TaskStatus.IN_PROGRESS.value else "🔒" if child['status'] == TaskStatus.BLOCKED.value else "📋"
        print(f"    ├── {status_emoji} {child['title']}")
    
    # 12. Get critical path
    print("\n12. Analyzing Critical Path")
    print("-" * 50)
    
    critical_path = task_tool.get_critical_path(project["id"])
    
    print("Critical path for project completion:")
    for i, task in enumerate(critical_path):
        estimated = f"(Est: {task['estimated_effort']} hrs)" if task['estimated_effort'] else ""
        print(f"  {i+1}. {task['title']} {estimated}")
    
    # 13. Generate summary report
    print("\n13. Generating Project Summary Report")
    print("-" * 50)
    
    report = task_tool.generate_summary_report()
    
    print("Project Status Summary:")
    print(f"  Total Tasks: {report['total_tasks']}")
    print(f"  Overall Progress: {report['overall_progress']:.1f}%")
    print("\nTask Status Breakdown:")
    
    for status, count in report["status_breakdown"].items():
        if count > 0:
            print(f"  {TaskStatus(status).name}: {count} tasks")
    
    print(f"\nHigh Priority Tasks Pending: {report['high_priority_pending_count']}")
    print(f"Blocked Tasks: {report['blocked_tasks_count']}")
    print(f"Ready to Work On: {report['ready_tasks_count']}")

if __name__ == "__main__":
    main()