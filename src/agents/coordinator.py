import logging
from src.tools.llm_service import initialize_llm_service

# Import agent classes are already defined below in this file
# Circular import issue fixed by having agent classes in the same file

# Set up logging
logger = logging.getLogger(__name__)

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
        try:
            self.agents['planner'] = PlannerAgent(self.llm_service)
            self.agents['executor'] = ExecutionAgent(self.llm_service)
            self.agents['tool'] = ToolAgent(self.llm_service)
            logger.info("All agents initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing agents: {e}", exc_info=True)
            # Ensure agents dictionary is properly initialized even if some agents fail
            if 'planner' not in self.agents:
                self.agents['planner'] = None
            if 'executor' not in self.agents:
                self.agents['executor'] = None
            if 'tool' not in self.agents:
                self.agents['tool'] = None
        
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
            logger.warning(f"VectorDBTool could not be initialized: {e}")
            logger.info("Install required dependencies with: pip install faiss-cpu sentence-transformers")
            vector_db = None
            
        # Import StructuredDataTool
        try:
            from src.tools.structured_data.structured_data_tool import StructuredDataTool
            structured_data = StructuredDataTool()
        except ImportError as e:
            logger.warning(f"StructuredDataTool could not be initialized: {e}")
            logger.info("Install required dependencies with: pip install pandas matplotlib scipy")
            structured_data = None
            
        # Import MetadataExtractorTool
        try:
            from src.tools.metadata_extractor import MetadataExtractorTool
            metadata_extractor = MetadataExtractorTool()
        except ImportError as e:
            logger.warning(f"MetadataExtractorTool could not be initialized: {e}")
            metadata_extractor = None
            
        # Import TaskDecompositionTool
        try:
            from src.tools.task_decomposition import TaskDecompositionTool
            task_decomposition = TaskDecompositionTool()
        except ImportError as e:
            logger.warning(f"TaskDecompositionTool could not be initialized: {e}")
            task_decomposition = None
            
        # Import DocumentProcessingTool
        try:
            from src.tools.document_processing import DocumentProcessingTool
            document_processing = DocumentProcessingTool()
        except ImportError as e:
            logger.warning(f"DocumentProcessingTool could not be initialized: {e}")
            logger.info("Install required dependencies with: pip install PyPDF2 python-docx")
            document_processing = None
            
        tools = {
            'web_browser': WebBrowserTool(),
            'code_executor': CodeExecutorTool(),
            'data_retriever': DataRetrieverTool(),
            'memory': MemoryTool(),
            'file_manager': FileManagerTool(),
            'llm_service': self.llm_service
        }
        
        # Add tools if available
        if vector_db:
            tools['vector_db'] = vector_db
            
        if structured_data:
            tools['structured_data'] = structured_data
            
        if metadata_extractor:
            tools['metadata_extractor'] = metadata_extractor
            
        if task_decomposition:
            tools['task_decomposition'] = task_decomposition
            
        if document_processing:
            tools['document_processing'] = document_processing
            
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
            dict: Result of the task execution with status and details
        """
        try:
            # Log task start
            logger.info(f"Starting task execution: {task_description[:50]}...")
            
            # Generate execution plan
            try:
                plan = self.agents['planner'].plan_task(task_description)
                if not plan or not isinstance(plan, dict) or "steps" not in plan:
                    raise ValueError("Invalid plan format returned by planner agent")
            except Exception as e:
                logger.error(f"Error during planning phase: {str(e)}", exc_info=True)
                return {
                    "status": "error",
                    "phase": "planning",
                    "error": str(e),
                    "result": f"Failed to create execution plan: {str(e)}"
                }
            
            # Execute the plan
            try:
                result = self.agents['executor'].execute_plan(plan, self.agents, self.tools)
            except Exception as e:
                logger.error(f"Error during execution phase: {str(e)}", exc_info=True)
                return {
                    "status": "error",
                    "phase": "execution",
                    "error": str(e),
                    "plan": plan,
                    "result": f"Failed to execute plan: {str(e)}"
                }
                
            # Return successful result
            return {
                "status": "success",
                "result": result,
                "plan": plan
            }
        except Exception as e:
            # Catch-all for any unhandled exceptions
            logger.error(f"Unexpected error in task execution: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "phase": "unknown",
                "error": str(e),
                "result": f"An unexpected error occurred: {str(e)}"
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
                logger.error(f"Error generating plan with LLM: {e}", exc_info=True)
        
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
        """
        Executes a given task plan with improved error handling.
        
        Args:
            plan: The execution plan with steps
            agents: Dictionary of available agents
            tools: Dictionary of available tools
            
        Returns:
            String with execution results or error information
        """
        if not plan or not isinstance(plan, dict) or 'steps' not in plan:
            return "Error: Invalid plan format. Plan must be a dictionary with a 'steps' key."
        
        if not plan['steps'] or not isinstance(plan['steps'], list):
            return "Error: Plan steps must be a non-empty list."
        
        results = []
        for i, step in enumerate(plan['steps']):
            step_num = i + 1
            step_result = None
            
            try:
                # Validate step format
                if not isinstance(step, dict):
                    raise ValueError(f"Step {step_num} is not a dictionary")
                
                # Log step execution
                step_desc = f"Executing step {step_num}/{len(plan['steps'])}"
                logger.info(f"{step_desc}: {str(step)[:100]}...")
                
                # Extract step components with validation
                if 'agent' not in step:
                    raise ValueError(f"Step {step_num} is missing 'agent' field")
                agent_name = step['agent']
                
                if 'action' not in step:
                    raise ValueError(f"Step {step_num} is missing 'action' field")
                action = step['action']
                
                # Execute based on agent and action
                if agent_name == 'tool' and action == 'use_tool':
                    # Validate tool parameters
                    if 'tool_name' not in step:
                        raise ValueError(f"Step {step_num} is missing 'tool_name' field")
                    tool_name = step['tool_name']
                    
                    if 'tool_args' not in step:
                        raise ValueError(f"Step {step_num} is missing 'tool_args' field")
                    tool_args = step['tool_args']
                    
                    # Check if tool exists
                    if tool_name not in tools:
                        results.append(f"Warning in step {step_num}: Tool '{tool_name}' not found. Available tools: {', '.join(tools.keys())}")
                        continue
                    
                    # Execute tool with exception handling
                    try:
                        tool_result = agents['tool'].use_tool(tool_name, tool_args, tools)
                        step_result = tool_result
                    except Exception as tool_error:
                        error_msg = f"Error in step {step_num} using tool '{tool_name}': {str(tool_error)}"
                        logger.error(error_msg, exc_info=True)
                        results.append(error_msg)
                        continue
                    
                    # Summarize long results if LLM service is available
                    if self.llm_service and isinstance(tool_result, str) and len(tool_result) > 500:
                        try:
                            prompt = f"Summarize the following tool result concisely:\n{tool_result}"
                            summary = self.llm_service.generate(
                                prompt=prompt,
                                provider_name=self.llm_service.get_preferred_provider("executor", "agent").capabilities["type"]
                            )
                            results.append(f"Tool '{tool_name}' used with args {tool_args}. Result summary: {summary}")
                        except Exception as e:
                            logger.warning(f"Error summarizing result with LLM: {e}")
                            # Fallback to truncated result if summarization fails
                            trunc_result = tool_result[:500] + "..." if len(tool_result) > 500 else tool_result
                            results.append(f"Tool '{tool_name}' used with args {tool_args}. Result: {trunc_result}")
                    else:
                        # Format result based on type
                        if isinstance(tool_result, (dict, list)):
                            import json
                            formatted_result = json.dumps(tool_result, indent=2)
                            results.append(f"Tool '{tool_name}' used with args {tool_args}. Result:\n{formatted_result}")
                        else:
                            results.append(f"Tool '{tool_name}' used with args {tool_args}. Result: {tool_result}")
                else:
                    results.append(f"Unsupported step {step_num}: agent='{agent_name}', action='{action}'. Currently only tool agent with use_tool action is supported.")
            
            except Exception as step_error:
                error_msg = f"Error processing step {step_num}: {str(step_error)}"
                logger.error(error_msg, exc_info=True)
                results.append(error_msg)
        
        # Combine all results
        if not results:
            return "Warning: Plan executed but no results were produced."
        
        return "\n\n".join(results)


class ToolAgent:
    """Agent responsible for using tools."""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        
        # Define required parameters for each tool
        self.tool_required_params = {
            'web_browser': ['url'],
            'code_executor': ['code', 'language'],
            'data_retriever': ['query'],
            'llm_service': ['prompt']
        }
        
        # Define required parameters for each operation of complex tools
        self.operation_required_params = {
            'memory': {
                'store': ['content'],
                'get': ['memory_id'],
                'get_all': [],
                'search': ['query'],
                'update': ['memory_id'],
                'delete': ['memory_id'],
                'list_namespaces': [],
                'clear_namespace': ['namespace']
            },
            'vector_db': {
                'create_collection': ['collection_name'],
                'delete_collection': ['collection_name'],
                'list_collections': [],
                'add_text': ['collection_name', 'text'],
                'add_texts': ['collection_name', 'texts'],
                'search': ['collection_name', 'query'],
                'get_by_id': ['collection_name', 'doc_id'],
                'delete_by_id': ['collection_name', 'doc_id'],
                'clear_collection': ['collection_name'],
                'update_metadata': ['collection_name', 'doc_id', 'metadata'],
                'get_collection_stats': ['collection_name']
            },
            'file_manager': {
                'read_file': ['path'],
                'read_text': ['path'],
                'write_file': ['path', 'content'],
                'write_text': ['path', 'content'],
                'delete_file': ['path'],
                'list_files': ['path'],
                'file_exists': ['path'],
                'create_directory': ['path'],
                'rename_file': ['old_path', 'new_path'],
                'get_storage_preferences': [],
                'set_storage_preference': ['file_type', 'storage_type'],
                'get_file_history': ['path'],
                'initialize_backend': ['backend_type']
            }
        }
    
    def use_tool(self, tool_name, tool_args, tools):
        """
        Uses a specific tool to perform an action with improved error handling.
        
        Args:
            tool_name: Name of the tool to use
            tool_args: Arguments to pass to the tool
            tools: Dictionary of available tools
            
        Returns:
            The result of the tool operation or an error message
        """
        # Validate tool exists
        if tool_name not in tools:
            available_tools = ", ".join(tools.keys())
            return f"Error: Tool '{tool_name}' not found. Available tools: {available_tools}"
            
        # Get the tool
        try:
            tool = tools[tool_name]
        except Exception as e:
            return f"Error accessing tool '{tool_name}': {str(e)}"
            
        # Log tool usage
        logger.info(f"Using tool: {tool_name} with args: {tool_args}")
        
        # If using LLM with tools, get preferred provider
        if self.llm_service and tool_name in self.llm_service.tool_preferences:
            try:
                provider = self.llm_service.get_preferred_provider(tool_name, "tool")
                provider_type = provider.capabilities["type"]
                logger.info(f"Using {provider_type} for tool: {tool_name}")
            except Exception as e:
                logger.warning(f"Error getting preferred provider: {str(e)}")
                
        # Execute based on tool type
        try:
            # Simple tools
            if tool_name in ['web_browser', 'code_executor', 'data_retriever']:
                # Validate required parameters
                missing_params = self._check_missing_params(
                    tool_args, 
                    self.tool_required_params.get(tool_name, [])
                )
                if missing_params:
                    return f"Error: Tool '{tool_name}' is missing required parameters: {', '.join(missing_params)}"
                
                # Execute simple tool
                if tool_name == 'web_browser':
                    return tool.browse_web(**tool_args)
                elif tool_name == 'code_executor':
                    return tool.execute_code(**tool_args)
                elif tool_name == 'data_retriever':
                    return tool.retrieve_data(**tool_args)
                    
            # Tools with operations
            elif tool_name in ['memory', 'vector_db', 'file_manager']:
                # Validate operation parameter
                if 'operation' not in tool_args:
                    return f"Error: {tool_name.capitalize()} tool requires an 'operation' argument"
                    
                operation = tool_args.get('operation')
                
                # Check if operation is valid
                if operation not in self.operation_required_params.get(tool_name, {}):
                    valid_ops = ", ".join(self.operation_required_params.get(tool_name, {}).keys())
                    return f"Error: Unknown {tool_name} operation: '{operation}'. Valid operations: {valid_ops}"
                
                # Validate required parameters for this operation
                tool_args_copy = tool_args.copy()
                del tool_args_copy['operation']  # Remove operation for validation
                
                required_params = self.operation_required_params[tool_name][operation]
                missing_params = self._check_missing_params(tool_args_copy, required_params)
                if missing_params:
                    return f"Error: Operation '{operation}' requires parameters: {', '.join(missing_params)}"
                
                # Execute operations for specific tools
                return self._execute_tool_operation(tool, tool_name, operation, tool_args_copy)
                
            # LLM service
            elif tool_name == 'llm_service':
                if 'prompt' not in tool_args:
                    return "Error: LLM service requires a 'prompt' argument"
                
                provider = tool_args.get('provider', None)
                return tool.generate(tool_args['prompt'], provider_name=provider)
                
            # Unknown tool type
            else:
                return f"Error: Tool '{tool_name}' has no implementation defined."
                
        except Exception as e:
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def _check_missing_params(self, args, required_params):
        """Check for missing required parameters."""
        missing = []
        for param in required_params:
            if param not in args:
                missing.append(param)
        return missing
    
    def _execute_tool_operation(self, tool, tool_name, operation, args):
        """Execute a specific operation on a tool."""
        try:
            # Memory tool operations
            if tool_name == 'memory':
                if operation == 'store':
                    result = tool.store(**args)
                    return f"Memory stored with ID: {result['id']}"
                    
                elif operation == 'get':
                    result = tool.get(**args)
                    return result if result else "Memory not found"
                    
                elif operation == 'get_all':
                    result = tool.get_all(**args)
                    return f"Retrieved {len(result)} memories"
                    
                elif operation == 'search':
                    result = tool.search(**args)
                    if not result:
                        return "No matching memories found"
                    return f"Found {len(result)} matching memories: {result}"
                    
                elif operation == 'update':
                    result = tool.update(**args)
                    return "Memory updated successfully" if result else "Memory not found or update failed"
                    
                elif operation == 'delete':
                    result = tool.delete(**args)
                    return "Memory deleted successfully" if result else "Memory not found or delete failed"
                    
                elif operation == 'list_namespaces':
                    result = tool.list_namespaces()
                    if not result:
                        return "No namespaces found"
                    return f"Available namespaces: {result}"
                    
                elif operation == 'clear_namespace':
                    result = tool.clear_namespace(**args)
                    return "Namespace cleared successfully" if result else "Namespace not found or clear failed"
            
            # Vector DB tool operations
            elif tool_name == 'vector_db':
                if operation == 'create_collection':
                    result = tool.create_collection(**args)
                    return f"Collection created: {result}"
                    
                elif operation == 'delete_collection':
                    result = tool.delete_collection(**args)
                    return f"Collection deleted: {result}"
                    
                elif operation == 'list_collections':
                    result = tool.list_collections()
                    if not result:
                        return "No collections found"
                    return f"Available collections: {result}"
                    
                elif operation == 'add_text':
                    result = tool.add_text(**args)
                    if not result:
                        return "Failed to add document"
                    return f"Document added with ID: {result}"
                    
                elif operation == 'add_texts':
                    result = tool.add_texts(**args)
                    if not result:
                        return "Failed to add documents"
                    return f"Added {len(result)} documents with IDs: {result}"
                    
                elif operation == 'search':
                    result = tool.search(**args)
                    if not result:
                        return "No similar documents found"
                    return f"Found {len(result)} similar documents: {result}"
                    
                elif operation == 'get_by_id':
                    result = tool.get_by_id(**args)
                    return result if result else "Document not found"
                    
                elif operation == 'delete_by_id':
                    result = tool.delete_by_id(**args)
                    return "Document deleted successfully" if result else "Document not found or delete failed"
                    
                elif operation == 'clear_collection':
                    result = tool.clear_collection(**args)
                    return "Collection cleared successfully" if result else "Collection not found or clear failed"
                    
                elif operation == 'update_metadata':
                    result = tool.update_metadata(**args)
                    return "Metadata updated successfully" if result else "Document not found or update failed"
                    
                elif operation == 'get_collection_stats':
                    result = tool.get_collection_stats(**args)
                    return f"Collection stats: {result}" if result else "Collection not found"
            
            # File manager operations
            elif tool_name == 'file_manager':
                if operation == 'read_file':
                    result = tool.read_file(**args)
                    if result is None:
                        return "Error: File not found or cannot be read"
                    return f"File read successfully ({len(result)} bytes)"
                    
                elif operation == 'read_text':
                    result = tool.read_text(**args)
                    if result is None:
                        return "Error: File not found or cannot be read"
                    preview = result[:100] + "..." if len(result) > 100 else result
                    return f"File content: {preview}"
                    
                elif operation == 'write_file':
                    result = tool.write_file(**args)
                    if not result:
                        return "Error: Failed to write file"
                    return f"File written successfully to: {args.get('path')}"
                    
                elif operation == 'write_text':
                    result = tool.write_text(**args)
                    if not result:
                        return "Error: Failed to write file"
                    return f"File written successfully to: {args.get('path')}"
                    
                elif operation == 'delete_file':
                    result = tool.delete_file(**args)
                    if not result:
                        return "Error: File not found or cannot be deleted"
                    return f"File deleted successfully: {args.get('path')}"
                    
                elif operation == 'list_files':
                    result = tool.list_files(**args)
                    if not result:
                        return "No files found in the specified path"
                    return f"Found {len(result)} files: {result}"
                    
                elif operation == 'file_exists':
                    result = tool.file_exists(**args)
                    return f"File exists: {result}"
                    
                elif operation == 'create_directory':
                    result = tool.create_directory(**args)
                    if not result:
                        return "Error: Failed to create directory"
                    return f"Directory created successfully: {args.get('path')}"
                    
                elif operation == 'rename_file':
                    result = tool.rename_file(**args)
                    if not result:
                        return "Error: File not found or cannot be renamed"
                    return f"File renamed successfully from {args.get('old_path')} to {args.get('new_path')}"
                    
                elif operation == 'get_storage_preferences':
                    result = tool.get_storage_preferences()
                    return f"Storage preferences: {result}"
                    
                elif operation == 'set_storage_preference':
                    result = tool.set_storage_preference(**args)
                    if not result:
                        return "Error: Failed to update storage preference"
                    return f"Storage preference updated successfully for file type: {args.get('file_type')}"
                    
                elif operation == 'get_file_history':
                    result = tool.get_file_history(**args)
                    if not result:
                        return "No file history found"
                    return f"File history: {result}"
                    
                elif operation == 'initialize_backend':
                    result = tool.initialize_backend(**args)
                    if not result:
                        return f"Error: Failed to initialize backend: {args.get('backend_type')}"
                    return f"Backend initialized successfully: {args.get('backend_type')}"
            
            # Should never reach here due to validation
            return f"Error: Unknown operation for {tool_name}: {operation}"
            
        except AttributeError as e:
            return f"Error: Tool does not support operation '{operation}': {str(e)}"
        except TypeError as e:
            return f"Error: Invalid parameters for operation '{operation}': {str(e)}"
        except Exception as e:
            return f"Error executing {tool_name} operation '{operation}': {str(e)}"