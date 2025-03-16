from src.tools.llm_service import initialize_llm_service

class TaskCoordinator:
    """Coordinates tasks between multiple agents and tools."""

    def __init__(self):
        self.agents = {}  # Will store initialized agents
        self.tools = {}   # Will store available tools
        self.llm_service = None
        self._initialize_system()

    def _initialize_system(self):
        """Initialize the multi-agent system and tools."""
        # Initialize LLM service first
        self.llm_service = initialize_llm_service()
        
        # Initialize agents with LLM service
        self.agents['planner'] = PlannerAgent(self.llm_service)
        self.agents['executor'] = ExecutionAgent(self.llm_service)
        self.agents['tool'] = ToolAgent(self.llm_service)
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Set default LLM preferences for agents and tools
        self._set_default_preferences()

    def _initialize_tools(self):
        """Initialize and return available tools."""
        from src.tools.web_browser import WebBrowserTool
        from src.tools.code_executor import CodeExecutorTool
        from src.tools.data_retriever import DataRetrieverTool
        from src.tools.memory_tool import MemoryTool
        from src.tools.file_manager import FileManagerTool
        
        # Import VectorDBTool with error handling since it has extra dependencies
        try:
            from src.tools.vector_db_tool import VectorDBTool
            vector_db = VectorDBTool()
        except ImportError as e:
            print(f"VectorDBTool could not be initialized: {e}")
            print("Install required dependencies with: pip install faiss-cpu sentence-transformers")
            vector_db = None
            
        tools = {
            'web_browser': WebBrowserTool(),
            'code_executor': CodeExecutorTool(),
            'data_retriever': DataRetrieverTool(),
            'memory': MemoryTool(),
            'file_manager': FileManagerTool(),
            'llm_service': self.llm_service
        }
        
        # Add vector_db if available
        if vector_db:
            tools['vector_db'] = vector_db
            
        return tools
    
    def _set_default_preferences(self):
        """Set default LLM preferences for agents and tools."""
        # Only set preferences if we have appropriate providers available
        providers = self.llm_service.list_providers()
        available_providers = [p["name"] for p in providers]
        
        # Set default preferences if providers are available
        if "gpt4o" in available_providers:
            self.llm_service.set_agent_preference(
                "planner", "gpt4o", 
                "GPT-4o is well-suited for complex planning tasks requiring reasoning"
            )
        
        if "claude" in available_providers:
            self.llm_service.set_agent_preference(
                "executor", "claude", 
                "Claude's safety and reliability make it good for execution"
            )
            
        if "local" in available_providers:
            self.llm_service.set_tool_preference(
                "web_browser", "local", 
                "Local LLM is sufficient for basic web parsing and reduces costs"
            )
            
            self.llm_service.set_tool_preference(
                "memory", "local",
                "Local LLM is ideal for memory operations to ensure privacy and reduce costs"
            )

    def execute_task(self, task_description):
        """
        Execute a task using the multi-agent system.

        Args:
            task_description (str): Natural language description of the task

        Returns:
            dict: Result of the task execution
        """
        plan = self.agents['planner'].plan_task(task_description)
        result = self.agents['executor'].execute_plan(plan, self.agents, self.tools)
        return {
            "status": "success",
            "result": result
        }
    
    def set_llm_preference(self, entity_type, entity_name, provider_name, reason=""):
        """
        Set LLM preference for a specific agent or tool.
        
        Args:
            entity_type (str): Either 'agent' or 'tool'
            entity_name (str): Name of the agent or tool
            provider_name (str): Name of the LLM provider
            reason (str): Reason for this preference
        """
        if entity_type == "agent":
            self.llm_service.set_agent_preference(entity_name, provider_name, reason)
        elif entity_type == "tool":
            self.llm_service.set_tool_preference(entity_name, provider_name, reason)
        else:
            raise ValueError(f"Invalid entity type: {entity_type}")
    
    def get_provider_recommendations(self):
        """Get LLM provider recommendations for agents and tools."""
        recommendations = {
            "providers": self.llm_service.list_providers(),
            "agent_preferences": self.llm_service.agent_preferences,
            "tool_preferences": self.llm_service.tool_preferences
        }
        return recommendations


class PlannerAgent:
    """Agent responsible for planning tasks."""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
    
    def plan_task(self, task_description):
        """Generates a task execution plan."""
        # If we have LLM service, use it to generate a plan
        if self.llm_service:
            try:
                # Get preferred provider for this agent
                prompt = f"""
                Generate a step-by-step execution plan for the following task:
                "{task_description}"
                
                The plan should use available tools:
                1. web_browser - Browse websites and extract information
                2. code_executor - Execute code snippets in various languages
                3. data_retriever - Retrieve data from various sources
                4. memory - Store and retrieve information across sessions
                5. vector_db - Semantic search using vector embeddings
                6. file_manager - Read, write, and manage files with multiple storage backends
                
                Memory tool supports the following operations:
                - store: Store information (content, metadata, namespace)
                - get: Get specific memory by ID
                - get_all: Get all memories in a namespace
                - search: Search memories by query
                - update: Update existing memory
                - delete: Delete a memory
                - list_namespaces: List all available namespaces
                
                Vector DB tool supports the following operations:
                - create_collection: Create a new vector collection
                - delete_collection: Delete a collection
                - list_collections: List all available collections
                - add_text: Add text to a collection (with optional metadata)
                - add_texts: Add multiple texts to a collection (batch operation)
                - search: Semantic search for similar documents
                - get_by_id: Get document by ID
                - delete_by_id: Delete document by ID
                - clear_collection: Clear all documents from a collection
                - update_metadata: Update metadata for a document
                - get_collection_stats: Get collection statistics
                
                File Manager tool supports the following operations:
                - read_file: Read a file as bytes (path, storage_type, file_type)
                - read_text: Read a file as text (path, storage_type, file_type, encoding)
                - write_file: Write bytes to a file (path, content, storage_type, file_type, metadata)
                - write_text: Write text to a file (path, content, storage_type, file_type, encoding, metadata)
                - delete_file: Delete a file (path, storage_type, file_type, metadata)
                - list_files: List files in a directory (path, storage_type, file_type)
                - file_exists: Check if a file exists (path, storage_type, file_type)
                - create_directory: Create a directory (path, storage_type, file_type)
                - rename_file: Rename or move a file (old_path, new_path, storage_type, file_type, metadata)
                - get_storage_preferences: Get current storage preferences 
                - set_storage_preference: Set storage preference for a file type (file_type, storage_type)
                - get_file_history: Get file history for git-stored files (path, max_entries)
                
                File Manager supports multiple storage backends:
                - local: For temporary or short-term files
                - git: For code and knowledge base files (with versioning)
                - google_drive: For long-term storage (requires initialization)
                - onedrive: Alternative cloud storage (requires initialization)
                
                Return a JSON object with the following structure:
                {{
                    "steps": [
                        {{"agent": "tool", "action": "use_tool", "tool_name": "web_browser", "tool_args": {{"url": "example.com"}}}},
                        {{"agent": "tool", "action": "use_tool", "tool_name": "memory", "tool_args": {{"operation": "store", "content": "Important information", "namespace": "research"}}}},
                        {{"agent": "tool", "action": "use_tool", "tool_name": "vector_db", "tool_args": {{"operation": "add_text", "collection_name": "docs", "text": "Document content", "metadata": {{"source": "web"}}}}}},
                        {{"agent": "tool", "action": "use_tool", "tool_name": "file_manager", "tool_args": {{"operation": "write_text", "path": "report.md", "content": "# Report", "file_type": "document"}}}},
                        ...
                    ]
                }}
                
                ONLY return valid JSON without explanation or additional text.
                """
                
                # Generate plan using LLM
                result = self.llm_service.generate(
                    prompt=prompt,
                    provider_name=self.llm_service.get_preferred_provider("planner", "agent").capabilities["type"]
                )
                
                # Extract JSON from result (naive implementation - would be more robust in production)
                import json
                try:
                    # Try to find json between curly braces
                    start = result.find('{')
                    end = result.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = result[start:end]
                        return json.loads(json_str)
                except:
                    # Fallback to default plan if parsing fails
                    pass
            except Exception as e:
                print(f"Error generating plan with LLM: {e}")
        
        # Fallback plan if LLM is not available or fails
        # Include memory and file_manager operations to demonstrate basic functionality
        return {
            "steps": [
                {"agent": "tool", "action": "use_tool", "tool_name": "memory", "tool_args": {"operation": "store", "content": f"Task received: {task_description}", "namespace": "tasks"}},
                {"agent": "tool", "action": "use_tool", "tool_name": "web_browser", "tool_args": {"url": "https://www.example.com"}},
                {"agent": "tool", "action": "use_tool", "tool_name": "file_manager", "tool_args": {"operation": "write_text", "path": "task_log.txt", "content": f"Task executed: {task_description}", "file_type": "temp"}},
                {"agent": "tool", "action": "use_tool", "tool_name": "memory", "tool_args": {"operation": "search", "query": "Task", "namespace": "tasks"}}
            ]
        }


class ExecutionAgent:
    """Agent responsible for executing task plans."""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
    
    def execute_plan(self, plan, agents, tools):
        """Executes a given task plan."""
        results = []
        for step in plan['steps']:
            agent_name = step['agent']
            action = step['action']
            if agent_name == 'tool' and action == 'use_tool':
                tool_name = step['tool_name']
                tool_args = step['tool_args']
                tool_result = agents['tool'].use_tool(tool_name, tool_args, tools)
                
                # Use LLM to summarize the tool result if available
                if self.llm_service and len(str(tool_result)) > 500:
                    try:
                        prompt = f"Summarize the following tool result concisely:\n{tool_result}"
                        summary = self.llm_service.generate(
                            prompt=prompt,
                            provider_name=self.llm_service.get_preferred_provider("executor", "agent").capabilities["type"]
                        )
                        results.append(f"Tool '{tool_name}' used with args {tool_args}. Result summary: {summary}")
                    except Exception as e:
                        print(f"Error summarizing result with LLM: {e}")
                        results.append(f"Tool '{tool_name}' used with args {tool_args}. Result: {tool_result}")
                else:
                    results.append(f"Tool '{tool_name}' used with args {tool_args}. Result: {tool_result}")
            else:
                results.append(f"Unknown step: {step}")
        return "\n".join(results)


class ToolAgent:
    """Agent responsible for using tools."""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
    
    def use_tool(self, tool_name, tool_args, tools):
        """Uses a specific tool to perform an action."""
        if tool_name in tools:
            tool = tools[tool_name]
            
            # If using LLM with tools, get preferred provider
            if self.llm_service and tool_name in self.llm_service.tool_preferences:
                provider_type = self.llm_service.get_preferred_provider(tool_name, "tool").capabilities["type"]
                print(f"Using {provider_type} for tool: {tool_name}")
                
            # Execute the tool
            if tool_name == 'web_browser':
                return tool.browse_web(**tool_args)
            elif tool_name == 'code_executor':
                return tool.execute_code(**tool_args)
            elif tool_name == 'data_retriever':
                return tool.retrieve_data(**tool_args)
            elif tool_name == 'memory':
                # Handle memory tool operations
                operation = tool_args.get('operation')
                if not operation:
                    return "Error: Memory tool requires an 'operation' argument"
                
                # Remove operation from args since it's not a parameter of the methods
                tool_args_copy = tool_args.copy()
                del tool_args_copy['operation']
                
                # Call the appropriate method based on operation
                if operation == 'store':
                    result = tool.store(**tool_args_copy)
                    return f"Memory stored with ID: {result['id']}"
                elif operation == 'get':
                    result = tool.get(**tool_args_copy)
                    return result if result else "Memory not found"
                elif operation == 'get_all':
                    result = tool.get_all(**tool_args_copy)
                    return f"Retrieved {len(result)} memories"
                elif operation == 'search':
                    result = tool.search(**tool_args_copy)
                    return f"Found {len(result)} matching memories: {result}"
                elif operation == 'update':
                    result = tool.update(**tool_args_copy)
                    return "Memory updated successfully" if result else "Memory not found"
                elif operation == 'delete':
                    result = tool.delete(**tool_args_copy)
                    return "Memory deleted successfully" if result else "Memory not found"
                elif operation == 'list_namespaces':
                    result = tool.list_namespaces()
                    return f"Available namespaces: {result}"
                elif operation == 'clear_namespace':
                    result = tool.clear_namespace(**tool_args_copy)
                    return "Namespace cleared successfully" if result else "Namespace not found"
                else:
                    return f"Unknown memory operation: {operation}"
            elif tool_name == 'vector_db':
                # Handle vector database operations
                operation = tool_args.get('operation')
                if not operation:
                    return "Error: VectorDB tool requires an 'operation' argument"
                
                # Remove operation from args since it's not a parameter of the methods
                tool_args_copy = tool_args.copy()
                del tool_args_copy['operation']
                
                # Call the appropriate method based on operation
                if operation == 'create_collection':
                    result = tool.create_collection(**tool_args_copy)
                    return f"Collection created: {result}"
                elif operation == 'delete_collection':
                    result = tool.delete_collection(**tool_args_copy)
                    return f"Collection deleted: {result}"
                elif operation == 'list_collections':
                    result = tool.list_collections()
                    return f"Available collections: {result}"
                elif operation == 'add_text':
                    result = tool.add_text(**tool_args_copy)
                    return f"Document added with ID: {result}"
                elif operation == 'add_texts':
                    result = tool.add_texts(**tool_args_copy)
                    return f"Added {len(result)} documents with IDs: {result}"
                elif operation == 'search':
                    result = tool.search(**tool_args_copy)
                    return f"Found {len(result)} similar documents: {result}"
                elif operation == 'get_by_id':
                    result = tool.get_by_id(**tool_args_copy)
                    return result if result else "Document not found"
                elif operation == 'delete_by_id':
                    result = tool.delete_by_id(**tool_args_copy)
                    return "Document deleted successfully" if result else "Document not found"
                elif operation == 'clear_collection':
                    result = tool.clear_collection(**tool_args_copy)
                    return "Collection cleared successfully" if result else "Collection not found"
                elif operation == 'update_metadata':
                    result = tool.update_metadata(**tool_args_copy)
                    return "Metadata updated successfully" if result else "Document not found"
                elif operation == 'get_collection_stats':
                    result = tool.get_collection_stats(**tool_args_copy)
                    return f"Collection stats: {result}" if result else "Collection not found"
                else:
                    return f"Unknown vector_db operation: {operation}"
            elif tool_name == 'file_manager':
                # Handle file manager operations
                operation = tool_args.get('operation')
                if not operation:
                    return "Error: FileManager tool requires an 'operation' argument"
                
                # Remove operation from args since it's not a parameter of the methods
                tool_args_copy = tool_args.copy()
                del tool_args_copy['operation']
                
                # Call the appropriate method based on operation
                if operation == 'read_file':
                    result = tool.read_file(**tool_args_copy)
                    if result is None:
                        return "Error reading file"
                    return f"File read successfully ({len(result)} bytes)"
                    
                elif operation == 'read_text':
                    result = tool.read_text(**tool_args_copy)
                    if result is None:
                        return "Error reading file"
                    preview = result[:100] + "..." if len(result) > 100 else result
                    return f"File content: {preview}"
                    
                elif operation == 'write_file':
                    result = tool.write_file(**tool_args_copy)
                    return "File written successfully" if result else "Error writing file"
                    
                elif operation == 'write_text':
                    result = tool.write_text(**tool_args_copy)
                    return "File written successfully" if result else "Error writing file"
                    
                elif operation == 'delete_file':
                    result = tool.delete_file(**tool_args_copy)
                    return "File deleted successfully" if result else "Error deleting file or file not found"
                    
                elif operation == 'list_files':
                    result = tool.list_files(**tool_args_copy)
                    return f"Found {len(result)} files: {result}"
                    
                elif operation == 'file_exists':
                    result = tool.file_exists(**tool_args_copy)
                    return f"File exists: {result}"
                    
                elif operation == 'create_directory':
                    result = tool.create_directory(**tool_args_copy)
                    return "Directory created successfully" if result else "Error creating directory"
                    
                elif operation == 'rename_file':
                    result = tool.rename_file(**tool_args_copy)
                    return "File renamed successfully" if result else "Error renaming file or file not found"
                    
                elif operation == 'get_storage_preferences':
                    result = tool.get_storage_preferences()
                    return f"Storage preferences: {result}"
                    
                elif operation == 'set_storage_preference':
                    result = tool.set_storage_preference(**tool_args_copy)
                    return "Storage preference updated successfully" if result else "Error updating storage preference"
                    
                elif operation == 'get_file_history':
                    result = tool.get_file_history(**tool_args_copy)
                    return f"File history: {result}"
                    
                elif operation == 'initialize_backend':
                    result = tool.initialize_backend(**tool_args_copy)
                    return "Backend initialized successfully" if result else "Error initializing backend"
                    
                else:
                    return f"Unknown file_manager operation: {operation}"
                    
            elif tool_name == 'llm_service':
                # Direct access to LLM service as a tool
                if 'prompt' in tool_args:
                    provider = tool_args.get('provider', None)
                    return tool.generate(tool_args['prompt'], provider_name=provider)
                else:
                    return "Error: LLM service requires a 'prompt' argument"
            else:
                return f"Tool '{tool_name}' not yet fully implemented."
        else:
            return f"Tool '{tool_name}' not found."