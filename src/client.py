import argparse
import requests
import json
import sys

def submit_task(task, host="http://localhost:5000"):
    """Submit a task to the agent server."""
    try:
        response = requests.post(f"{host}/task", json={"task": task})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_status(host="http://localhost:5000"):
    """Get server status and LLM provider information."""
    try:
        response = requests.get(f"{host}/status")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_llm_providers(host="http://localhost:5000"):
    """Get available LLM providers with capabilities."""
    try:
        response = requests.get(f"{host}/llm/providers")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_llm_recommendations(host="http://localhost:5000"):
    """Get current LLM recommendations for agents and tools."""
    try:
        response = requests.get(f"{host}/llm/recommendations")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def set_llm_preference(entity_type, entity_name, provider_name, reason="", host="http://localhost:5000"):
    """Set LLM preference for a specific agent or tool."""
    try:
        data = {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "provider_name": provider_name,
            "reason": reason
        }
        response = requests.post(f"{host}/llm/preference", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="OpenManus CLI Client")
    parser.add_argument("--host", default="http://localhost:5000", help="Agent server host")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Task command
    task_parser = subparsers.add_parser("task", help="Submit a task")
    task_parser.add_argument("--task", required=True, help="Task description")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Get server status")
    
    # LLM provider commands
    llm_parser = subparsers.add_parser("llm", help="LLM operations")
    llm_subparsers = llm_parser.add_subparsers(dest="llm_command", help="LLM command")
    
    # LLM list command
    llm_list_parser = llm_subparsers.add_parser("list", help="List available LLM providers")
    
    # LLM recommendations command
    llm_rec_parser = llm_subparsers.add_parser("recommendations", help="Get LLM recommendations")
    
    # LLM preference command
    llm_pref_parser = llm_subparsers.add_parser("preference", help="Set LLM preference")
    llm_pref_parser.add_argument("--type", required=True, choices=["agent", "tool"], help="Entity type (agent or tool)")
    llm_pref_parser.add_argument("--name", required=True, help="Entity name (e.g., planner, web_browser)")
    llm_pref_parser.add_argument("--provider", required=True, help="Provider name (e.g., gpt4o, claude, local)")
    llm_pref_parser.add_argument("--reason", default="", help="Reason for preference")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Process commands
    if args.command == "task":
        result = submit_task(args.task, args.host)
        print(json.dumps(result, indent=2))
    elif args.command == "status":
        result = get_status(args.host)
        print(json.dumps(result, indent=2))
    elif args.command == "llm":
        if args.llm_command == "list":
            result = get_llm_providers(args.host)
            print(json.dumps(result, indent=2))
        elif args.llm_command == "recommendations":
            result = get_llm_recommendations(args.host)
            print(json.dumps(result, indent=2))
        elif args.llm_command == "preference":
            result = set_llm_preference(
                args.type, args.name, args.provider, args.reason, args.host
            )
            print(json.dumps(result, indent=2))
        else:
            llm_parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()