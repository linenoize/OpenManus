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

# Memory-related functions
def list_memory_namespaces(host="http://localhost:5000"):
    """List all memory namespaces."""
    try:
        response = requests.get(f"{host}/memory")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_memories(namespace, host="http://localhost:5000"):
    """Get all memories in a namespace."""
    try:
        response = requests.get(f"{host}/memory/{namespace}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def search_memories(namespace, query, host="http://localhost:5000"):
    """Search memories in a namespace."""
    try:
        response = requests.get(f"{host}/memory/{namespace}/search", params={"query": query})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def store_memory(namespace, content, metadata=None, memory_id=None, host="http://localhost:5000"):
    """Store a memory in a namespace."""
    try:
        data = {
            "content": content,
            "metadata": metadata,
            "memory_id": memory_id
        }
        response = requests.post(f"{host}/memory/{namespace}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_memory(namespace, memory_id, host="http://localhost:5000"):
    """Get a specific memory by ID."""
    try:
        response = requests.get(f"{host}/memory/{namespace}/{memory_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def update_memory(namespace, memory_id, content=None, metadata=None, host="http://localhost:5000"):
    """Update a memory."""
    try:
        data = {}
        if content:
            data["content"] = content
        if metadata:
            data["metadata"] = metadata
            
        response = requests.put(f"{host}/memory/{namespace}/{memory_id}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def delete_memory(namespace, memory_id, host="http://localhost:5000"):
    """Delete a memory."""
    try:
        response = requests.delete(f"{host}/memory/{namespace}/{memory_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def clear_namespace(namespace, host="http://localhost:5000"):
    """Clear all memories in a namespace."""
    try:
        response = requests.delete(f"{host}/memory/{namespace}")
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
    
    # Memory commands
    memory_parser = subparsers.add_parser("memory", help="Memory operations")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command", help="Memory command")
    
    # Memory list namespaces command
    memory_list_parser = memory_subparsers.add_parser("list", help="List memory namespaces")
    
    # Memory get all command
    memory_get_all_parser = memory_subparsers.add_parser("get-all", help="Get all memories in a namespace")
    memory_get_all_parser.add_argument("--namespace", required=True, help="Memory namespace")
    
    # Memory search command
    memory_search_parser = memory_subparsers.add_parser("search", help="Search memories")
    memory_search_parser.add_argument("--namespace", required=True, help="Memory namespace")
    memory_search_parser.add_argument("--query", required=True, help="Search query")
    
    # Memory store command
    memory_store_parser = memory_subparsers.add_parser("store", help="Store a memory")
    memory_store_parser.add_argument("--namespace", required=True, help="Memory namespace")
    memory_store_parser.add_argument("--content", required=True, help="Memory content")
    memory_store_parser.add_argument("--metadata", help="Memory metadata (JSON string)")
    memory_store_parser.add_argument("--id", help="Memory ID (optional)")
    
    # Memory get command
    memory_get_parser = memory_subparsers.add_parser("get", help="Get a specific memory")
    memory_get_parser.add_argument("--namespace", required=True, help="Memory namespace")
    memory_get_parser.add_argument("--id", required=True, help="Memory ID")
    
    # Memory update command
    memory_update_parser = memory_subparsers.add_parser("update", help="Update a memory")
    memory_update_parser.add_argument("--namespace", required=True, help="Memory namespace")
    memory_update_parser.add_argument("--id", required=True, help="Memory ID")
    memory_update_parser.add_argument("--content", help="New content")
    memory_update_parser.add_argument("--metadata", help="New metadata (JSON string)")
    
    # Memory delete command
    memory_delete_parser = memory_subparsers.add_parser("delete", help="Delete a memory")
    memory_delete_parser.add_argument("--namespace", required=True, help="Memory namespace")
    memory_delete_parser.add_argument("--id", required=True, help="Memory ID")
    
    # Memory clear namespace command
    memory_clear_parser = memory_subparsers.add_parser("clear", help="Clear a namespace")
    memory_clear_parser.add_argument("--namespace", required=True, help="Memory namespace")
    
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
    elif args.command == "memory":
        if args.memory_command == "list":
            result = list_memory_namespaces(args.host)
            print(json.dumps(result, indent=2))
        elif args.memory_command == "get-all":
            result = get_memories(args.namespace, args.host)
            print(json.dumps(result, indent=2))
        elif args.memory_command == "search":
            result = search_memories(args.namespace, args.query, args.host)
            print(json.dumps(result, indent=2))
        elif args.memory_command == "store":
            metadata = None
            if args.metadata:
                try:
                    metadata = json.loads(args.metadata)
                except json.JSONDecodeError:
                    print("Error: Metadata must be a valid JSON string")
                    sys.exit(1)
            
            result = store_memory(args.namespace, args.content, metadata, args.id, args.host)
            print(json.dumps(result, indent=2))
        elif args.memory_command == "get":
            result = get_memory(args.namespace, args.id, args.host)
            print(json.dumps(result, indent=2))
        elif args.memory_command == "update":
            metadata = None
            if args.metadata:
                try:
                    metadata = json.loads(args.metadata)
                except json.JSONDecodeError:
                    print("Error: Metadata must be a valid JSON string")
                    sys.exit(1)
                    
            result = update_memory(args.namespace, args.id, args.content, metadata, args.host)
            print(json.dumps(result, indent=2))
        elif args.memory_command == "delete":
            result = delete_memory(args.namespace, args.id, args.host)
            print(json.dumps(result, indent=2))
        elif args.memory_command == "clear":
            result = clear_namespace(args.namespace, args.host)
            print(json.dumps(result, indent=2))
        else:
            memory_parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()