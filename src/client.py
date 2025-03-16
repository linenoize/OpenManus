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

# File Manager related functions
def get_storage_preferences(host="http://localhost:5000"):
    """Get current file storage preferences."""
    try:
        response = requests.get(f"{host}/file-manager/preferences")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def set_storage_preference(file_type, storage_type, host="http://localhost:5000"):
    """Set storage preference for a file type."""
    try:
        data = {
            "file_type": file_type,
            "storage_type": storage_type
        }
        response = requests.post(f"{host}/file-manager/preferences", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def list_files(path="", storage_type=None, file_type=None, host="http://localhost:5000"):
    """List files in a directory."""
    try:
        params = {"path": path}
        if storage_type:
            params["storage_type"] = storage_type
        if file_type:
            params["file_type"] = file_type
            
        response = requests.get(f"{host}/file-manager/files", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def read_file(file_path, storage_type=None, file_type=None, as_text=True, encoding="utf-8", host="http://localhost:5000"):
    """Read a file."""
    try:
        params = {
            "as_text": "true" if as_text else "false"
        }
        if storage_type:
            params["storage_type"] = storage_type
        if file_type:
            params["file_type"] = file_type
        if encoding and as_text:
            params["encoding"] = encoding
            
        response = requests.get(f"{host}/file-manager/files/{file_path}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def write_file(path, content, storage_type=None, file_type=None, encoding="utf-8", metadata=None, host="http://localhost:5000"):
    """Write a file."""
    try:
        data = {
            "path": path,
            "content": content
        }
        if storage_type:
            data["storage_type"] = storage_type
        if file_type:
            data["file_type"] = file_type
        if encoding:
            data["encoding"] = encoding
        if metadata:
            data["metadata"] = metadata
            
        response = requests.post(f"{host}/file-manager/files", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def delete_file(file_path, storage_type=None, file_type=None, metadata=None, host="http://localhost:5000"):
    """Delete a file."""
    try:
        params = {}
        if storage_type:
            params["storage_type"] = storage_type
        if file_type:
            params["file_type"] = file_type
            
        response = requests.delete(f"{host}/file-manager/files/{file_path}", params=params, json=metadata)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def rename_file(file_path, new_path, storage_type=None, file_type=None, metadata=None, host="http://localhost:5000"):
    """Rename a file."""
    try:
        data = {
            "new_path": new_path
        }
        if storage_type:
            data["storage_type"] = storage_type
        if file_type:
            data["file_type"] = file_type
        if metadata:
            data["metadata"] = metadata
            
        response = requests.post(f"{host}/file-manager/files/{file_path}/rename", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def create_directory(path, storage_type=None, file_type=None, host="http://localhost:5000"):
    """Create a directory."""
    try:
        data = {
            "path": path
        }
        if storage_type:
            data["storage_type"] = storage_type
        if file_type:
            data["file_type"] = file_type
            
        response = requests.post(f"{host}/file-manager/directories", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_file_history(file_path, max_entries=10, host="http://localhost:5000"):
    """Get file history (git only)."""
    try:
        params = {
            "max_entries": max_entries
        }
        response = requests.get(f"{host}/file-manager/files/{file_path}/history", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def initialize_backend(backend_type, credentials_path, host="http://localhost:5000"):
    """Initialize a storage backend."""
    try:
        data = {
            "backend_type": backend_type,
            "credentials_path": credentials_path
        }
        response = requests.post(f"{host}/file-manager/backends", json=data)
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
    
    # File Manager commands
    file_manager_parser = subparsers.add_parser("file", help="File Manager operations")
    file_manager_subparsers = file_manager_parser.add_subparsers(dest="file_command", help="File Manager command")
    
    # List files command
    file_list_parser = file_manager_subparsers.add_parser("list", help="List files in a directory")
    file_list_parser.add_argument("--path", default="", help="Directory path")
    file_list_parser.add_argument("--storage", help="Storage type (local, git, google_drive, onedrive)")
    file_list_parser.add_argument("--type", help="File type (temp, code, knowledge, image, etc.)")
    
    # Read file command
    file_read_parser = file_manager_subparsers.add_parser("read", help="Read a file")
    file_read_parser.add_argument("--path", required=True, help="File path")
    file_read_parser.add_argument("--storage", help="Storage type (local, git, google_drive, onedrive)")
    file_read_parser.add_argument("--type", help="File type (temp, code, knowledge, image, etc.)")
    file_read_parser.add_argument("--binary", action="store_true", help="Read as binary")
    file_read_parser.add_argument("--encoding", default="utf-8", help="Text encoding")
    
    # Write file command
    file_write_parser = file_manager_subparsers.add_parser("write", help="Write a file")
    file_write_parser.add_argument("--path", required=True, help="File path")
    file_write_parser.add_argument("--content", required=True, help="File content")
    file_write_parser.add_argument("--storage", help="Storage type (local, git, google_drive, onedrive)")
    file_write_parser.add_argument("--type", help="File type (temp, code, knowledge, image, etc.)")
    file_write_parser.add_argument("--encoding", default="utf-8", help="Text encoding")
    file_write_parser.add_argument("--metadata", help="Metadata (JSON string, e.g. commit_message for git)")
    
    # Delete file command
    file_delete_parser = file_manager_subparsers.add_parser("delete", help="Delete a file")
    file_delete_parser.add_argument("--path", required=True, help="File path")
    file_delete_parser.add_argument("--storage", help="Storage type (local, git, google_drive, onedrive)")
    file_delete_parser.add_argument("--type", help="File type (temp, code, knowledge, image, etc.)")
    file_delete_parser.add_argument("--metadata", help="Metadata (JSON string)")
    
    # Rename file command
    file_rename_parser = file_manager_subparsers.add_parser("rename", help="Rename or move a file")
    file_rename_parser.add_argument("--path", required=True, help="Current file path")
    file_rename_parser.add_argument("--new-path", required=True, help="New file path")
    file_rename_parser.add_argument("--storage", help="Storage type (local, git, google_drive, onedrive)")
    file_rename_parser.add_argument("--type", help="File type (temp, code, knowledge, image, etc.)")
    file_rename_parser.add_argument("--metadata", help="Metadata (JSON string)")
    
    # Create directory command
    dir_create_parser = file_manager_subparsers.add_parser("mkdir", help="Create a directory")
    dir_create_parser.add_argument("--path", required=True, help="Directory path")
    dir_create_parser.add_argument("--storage", help="Storage type (local, git, google_drive, onedrive)")
    dir_create_parser.add_argument("--type", help="File type (temp, code, knowledge, image, etc.)")
    
    # Get file history command
    file_history_parser = file_manager_subparsers.add_parser("history", help="Get file history (git only)")
    file_history_parser.add_argument("--path", required=True, help="File path")
    file_history_parser.add_argument("--max", type=int, default=10, help="Maximum number of history entries")
    
    # Get storage preferences command
    pref_get_parser = file_manager_subparsers.add_parser("preferences", help="Get storage preferences")
    
    # Set storage preference command
    pref_set_parser = file_manager_subparsers.add_parser("set-preference", help="Set storage preference")
    pref_set_parser.add_argument("--file-type", required=True, help="File type (temp, code, knowledge, image, etc.)")
    pref_set_parser.add_argument("--storage", required=True, help="Storage type (local, git, google_drive, onedrive)")
    
    # Initialize backend command
    backend_init_parser = file_manager_subparsers.add_parser("init-backend", help="Initialize a storage backend")
    backend_init_parser.add_argument("--backend", required=True, choices=["google_drive", "onedrive"], help="Backend type")
    backend_init_parser.add_argument("--credentials", required=True, help="Path to credentials file")
    
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
    elif args.command == "file":
        if args.file_command == "list":
            result = list_files(args.path, args.storage, args.type, args.host)
            print(json.dumps(result, indent=2))
        elif args.file_command == "read":
            result = read_file(args.path, args.storage, args.type, 
                              not args.binary, args.encoding, args.host)
            print(json.dumps(result, indent=2))
        elif args.file_command == "write":
            metadata = None
            if args.metadata:
                try:
                    metadata = json.loads(args.metadata)
                except json.JSONDecodeError:
                    print("Error: Metadata must be a valid JSON string")
                    sys.exit(1)
                    
            result = write_file(args.path, args.content, args.storage, 
                               args.type, args.encoding, metadata, args.host)
            print(json.dumps(result, indent=2))
        elif args.file_command == "delete":
            metadata = None
            if args.metadata:
                try:
                    metadata = json.loads(args.metadata)
                except json.JSONDecodeError:
                    print("Error: Metadata must be a valid JSON string")
                    sys.exit(1)
                    
            result = delete_file(args.path, args.storage, args.type, metadata, args.host)
            print(json.dumps(result, indent=2))
        elif args.file_command == "rename":
            metadata = None
            if args.metadata:
                try:
                    metadata = json.loads(args.metadata)
                except json.JSONDecodeError:
                    print("Error: Metadata must be a valid JSON string")
                    sys.exit(1)
                    
            result = rename_file(args.path, args.new_path, args.storage, args.type, metadata, args.host)
            print(json.dumps(result, indent=2))
        elif args.file_command == "mkdir":
            result = create_directory(args.path, args.storage, args.type, args.host)
            print(json.dumps(result, indent=2))
        elif args.file_command == "history":
            result = get_file_history(args.path, args.max, args.host)
            print(json.dumps(result, indent=2))
        elif args.file_command == "preferences":
            result = get_storage_preferences(args.host)
            print(json.dumps(result, indent=2))
        elif args.file_command == "set-preference":
            result = set_storage_preference(args.file_type, args.storage, args.host)
            print(json.dumps(result, indent=2))
        elif args.file_command == "init-backend":
            result = initialize_backend(args.backend, args.credentials, args.host)
            print(json.dumps(result, indent=2))
        else:
            file_manager_parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()