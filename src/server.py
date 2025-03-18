from flask import Flask, request, jsonify
import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to track available modules and features
available_features = {
    'task_coordinator': False,
    'llm_service': False,
    'agents': {
        'planner': False,
        'executor': False,
        'tool': False
    },
    'tools': {}
}

# Initialize coordinator with error handling
try:
    from agents.coordinator import TaskCoordinator
    coordinator = TaskCoordinator()
    available_features['task_coordinator'] = True
    
    # Check which components were successfully initialized
    if coordinator.llm_service:
        available_features['llm_service'] = True
        
    for agent_name, agent in coordinator.agents.items():
        if agent:
            available_features['agents'][agent_name] = True
            
    for tool_name, tool in coordinator.tools.items():
        if tool:
            available_features['tools'][tool_name] = True
    
    logger.info("Coordinator initialized successfully")
except ImportError as e:
    logger.error(f"Failed to import TaskCoordinator: {e}")
    coordinator = None
except Exception as e:
    logger.error(f"Failed to initialize coordinator: {e}")
    coordinator = None

# Helper function to check if coordinator is available
def check_coordinator_available():
    """Check if the coordinator is available and return appropriate response if not"""
    if coordinator is None:
        return jsonify({
            'status': 'error',
            'error': 'Coordinator is not initialized',
            'message': 'The system is starting up or missing dependencies',
            'available_features': available_features
        }), 503
    return None

@app.route('/task', methods=['POST'])
def submit_task():
    # Check coordinator availability
    error_response = check_coordinator_available()
    if error_response:
        return error_response
        
    data = request.get_json()
    task = data.get('task')
    if not task:
        return jsonify({'error': 'No task provided'}), 400
    
    try:
        result = coordinator.execute_task(task)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Failed to execute task'
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get system status and initialization status"""
    # Basic status information that doesn't require the coordinator
    status_info = {
        'status': 'initializing' if coordinator is None else 'running',
        'available_features': available_features
    }
    
    # Add more details if coordinator is available
    if coordinator is not None and hasattr(coordinator, 'llm_service') and coordinator.llm_service:
        try:
            llm_providers = coordinator.llm_service.list_providers()
            providers_info = [p["name"] for p in llm_providers]
            status_info['llm_providers'] = providers_info
        except Exception as e:
            logger.error(f"Error getting LLM providers: {e}")
            status_info['llm_providers_error'] = str(e)
    
    return jsonify(status_info)

@app.route('/llm/providers', methods=['GET'])
def get_llm_providers():
    """Get all available LLM providers with capabilities"""
    # Check coordinator availability
    error_response = check_coordinator_available()
    if error_response:
        return error_response
        
    try:
        providers = coordinator.llm_service.list_providers()
        return jsonify({'providers': providers})
    except Exception as e:
        logger.error(f"Error getting LLM providers: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Failed to get LLM providers'
        }), 500

@app.route('/llm/recommendations', methods=['GET'])
def get_llm_recommendations():
    """Get current LLM recommendations for agents and tools"""
    # Check coordinator availability
    error_response = check_coordinator_available()
    if error_response:
        return error_response
        
    try:
        recommendations = coordinator.get_provider_recommendations()
        return jsonify(recommendations)
    except Exception as e:
        logger.error(f"Error getting LLM recommendations: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Failed to get LLM recommendations'
        }), 500

@app.route('/llm/preference', methods=['POST'])
def set_llm_preference():
    """Set LLM preference for a specific agent or tool"""
    # Check coordinator availability
    error_response = check_coordinator_available()
    if error_response:
        return error_response
        
    data = request.get_json()
    entity_type = data.get('entity_type')  # 'agent' or 'tool'
    entity_name = data.get('entity_name')  # e.g., 'planner', 'executor', 'web_browser'
    provider_name = data.get('provider_name')  # e.g., 'gpt4o', 'claude', 'local'
    reason = data.get('reason', '')  # Optional reason for the preference
    
    # Validate required parameters
    if not all([entity_type, entity_name, provider_name]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Validate entity_type
    if entity_type not in ['agent', 'tool']:
        return jsonify({'error': 'entity_type must be either "agent" or "tool"'}), 400
    
    try:
        coordinator.set_llm_preference(entity_type, entity_name, provider_name, reason)
        return jsonify({'status': 'success'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error setting LLM preference: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/memory', methods=['GET'])
def list_memory_namespaces():
    """List all memory namespaces"""
    # Check coordinator availability
    error_response = check_coordinator_available()
    if error_response:
        return error_response
        
    # Check if memory tool is available
    if 'memory' not in coordinator.tools or not coordinator.tools['memory']:
        return jsonify({
            'status': 'error',
            'error': 'Memory tool not available',
            'message': 'Memory tool is not initialized'
        }), 503
        
    try:
        namespaces = coordinator.tools['memory'].list_namespaces()
        return jsonify({'namespaces': namespaces})
    except Exception as e:
        logger.error(f"Error listing memory namespaces: {e}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@app.route('/memory/<namespace>', methods=['GET'])
def get_memories(namespace):
    """Get all memories in a namespace"""
    # Check coordinator availability
    error_response = check_coordinator_available()
    if error_response:
        return error_response
        
    # Check if memory tool is available
    if 'memory' not in coordinator.tools or not coordinator.tools['memory']:
        return jsonify({
            'status': 'error',
            'error': 'Memory tool not available',
            'message': 'Memory tool is not initialized'
        }), 503
        
    try:
        memories = coordinator.tools['memory'].get_all(namespace)
        return jsonify({'memories': memories})
    except Exception as e:
        logger.error(f"Error getting memories: {e}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@app.route('/memory/<namespace>/search', methods=['GET'])
def search_memories(namespace):
    """Search memories in a namespace"""
    # Check coordinator availability
    error_response = check_coordinator_available()
    if error_response:
        return error_response
        
    # Check if memory tool is available
    if 'memory' not in coordinator.tools or not coordinator.tools['memory']:
        return jsonify({
            'status': 'error',
            'error': 'Memory tool not available',
            'message': 'Memory tool is not initialized'
        }), 503
        
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        results = coordinator.tools['memory'].search(query, namespace)
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@app.route('/memory/<namespace>', methods=['POST'])
def store_memory(namespace):
    """Store a memory in a namespace"""
    # Check coordinator availability
    error_response = check_coordinator_available()
    if error_response:
        return error_response
        
    # Check if memory tool is available
    if 'memory' not in coordinator.tools or not coordinator.tools['memory']:
        return jsonify({
            'status': 'error',
            'error': 'Memory tool not available',
            'message': 'Memory tool is not initialized'
        }), 503
        
    data = request.get_json()
    content = data.get('content')
    metadata = data.get('metadata')
    memory_id = data.get('memory_id')
    
    if not content:
        return jsonify({'error': 'No content provided'}), 400
    
    try:
        memory = coordinator.tools['memory'].store(
            content=content,
            metadata=metadata,
            namespace=namespace,
            memory_id=memory_id
        )
        return jsonify({'status': 'success', 'memory': memory})
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@app.route('/memory/<namespace>/<memory_id>', methods=['GET'])
def get_memory(namespace, memory_id):
    """Get a specific memory by ID"""
    try:
        memory = coordinator.tools['memory'].get(memory_id, namespace)
        if not memory:
            return jsonify({'error': 'Memory not found'}), 404
        return jsonify({'memory': memory})
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/memory/<namespace>/<memory_id>', methods=['PUT'])
def update_memory(namespace, memory_id):
    """Update a memory"""
    data = request.get_json()
    content = data.get('content')
    metadata = data.get('metadata')
    
    if not content and not metadata:
        return jsonify({'error': 'No content or metadata provided'}), 400
    
    try:
        memory = coordinator.tools['memory'].update(
            memory_id=memory_id,
            content=content,
            metadata=metadata,
            namespace=namespace
        )
        
        if not memory:
            return jsonify({'error': 'Memory not found'}), 404
            
        return jsonify({'status': 'success', 'memory': memory})
    except Exception as e:
        logger.error(f"Error updating memory: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/memory/<namespace>/<memory_id>', methods=['DELETE'])
def delete_memory(namespace, memory_id):
    """Delete a memory"""
    try:
        result = coordinator.tools['memory'].delete(memory_id, namespace)
        if not result:
            return jsonify({'error': 'Memory not found'}), 404
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/memory/<namespace>', methods=['DELETE'])
def clear_namespace(namespace):
    """Clear all memories in a namespace"""
    try:
        result = coordinator.tools['memory'].clear_namespace(namespace)
        if not result:
            return jsonify({'error': 'Namespace not found'}), 404
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error clearing namespace: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Vector database endpoints
@app.route('/vector-db/collections', methods=['GET'])
def list_vector_collections():
    """List all vector collections"""
    try:
        if 'vector_db' not in coordinator.tools:
            return jsonify({'error': 'Vector database not available'}), 503
            
        collections = coordinator.tools['vector_db'].list_collections()
        return jsonify({'collections': collections})
    except Exception as e:
        logger.error(f"Error listing vector collections: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/vector-db/collections', methods=['POST'])
def create_vector_collection():
    """Create a new vector collection"""
    data = request.get_json()
    collection_name = data.get('collection_name')
    
    if not collection_name:
        return jsonify({'error': 'No collection name provided'}), 400
    
    try:
        if 'vector_db' not in coordinator.tools:
            return jsonify({'error': 'Vector database not available'}), 503
            
        result = coordinator.tools['vector_db'].create_collection(collection_name)
        if not result:
            return jsonify({'error': 'Collection already exists'}), 409
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error creating vector collection: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/vector-db/collections/<collection_name>', methods=['DELETE'])
def delete_vector_collection(collection_name):
    """Delete a vector collection"""
    try:
        if 'vector_db' not in coordinator.tools:
            return jsonify({'error': 'Vector database not available'}), 503
            
        result = coordinator.tools['vector_db'].delete_collection(collection_name)
        if not result:
            return jsonify({'error': 'Collection not found'}), 404
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error deleting vector collection: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/vector-db/collections/<collection_name>/stats', methods=['GET'])
def get_vector_collection_stats(collection_name):
    """Get statistics for a vector collection"""
    try:
        if 'vector_db' not in coordinator.tools:
            return jsonify({'error': 'Vector database not available'}), 503
            
        stats = coordinator.tools['vector_db'].get_collection_stats(collection_name)
        if not stats:
            return jsonify({'error': 'Collection not found'}), 404
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting vector collection stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/vector-db/collections/<collection_name>/documents', methods=['POST'])
def add_vector_document(collection_name):
    """Add a document to a vector collection"""
    data = request.get_json()
    text = data.get('text')
    metadata = data.get('metadata')
    external_id = data.get('external_id')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        if 'vector_db' not in coordinator.tools:
            return jsonify({'error': 'Vector database not available'}), 503
            
        doc_id = coordinator.tools['vector_db'].add_text(
            collection_name=collection_name,
            text=text,
            metadata=metadata,
            external_id=external_id
        )
        
        if not doc_id:
            return jsonify({'error': 'Failed to add document'}), 400
            
        return jsonify({'status': 'success', 'id': doc_id})
    except Exception as e:
        logger.error(f"Error adding vector document: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/vector-db/collections/<collection_name>/search', methods=['GET'])
def search_vector_collection(collection_name):
    """Search a vector collection"""
    query = request.args.get('query')
    k = request.args.get('k', 5, type=int)
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        if 'vector_db' not in coordinator.tools:
            return jsonify({'error': 'Vector database not available'}), 503
            
        results = coordinator.tools['vector_db'].search(
            collection_name=collection_name,
            query=query,
            k=k
        )
        
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"Error searching vector collection: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/vector-db/collections/<collection_name>/documents/<doc_id>', methods=['GET'])
def get_vector_document(collection_name, doc_id):
    """Get a document from a vector collection"""
    try:
        if 'vector_db' not in coordinator.tools:
            return jsonify({'error': 'Vector database not available'}), 503
            
        doc = coordinator.tools['vector_db'].get_by_id(collection_name, doc_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
            
        return jsonify({'document': doc})
    except Exception as e:
        logger.error(f"Error getting vector document: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/vector-db/collections/<collection_name>/documents/<doc_id>', methods=['PUT'])
def update_vector_document_metadata(collection_name, doc_id):
    """Update metadata for a document in a vector collection"""
    data = request.get_json()
    metadata = data.get('metadata')
    
    if not metadata:
        return jsonify({'error': 'No metadata provided'}), 400
    
    try:
        if 'vector_db' not in coordinator.tools:
            return jsonify({'error': 'Vector database not available'}), 503
            
        result = coordinator.tools['vector_db'].update_metadata(
            collection_name=collection_name,
            doc_id=doc_id,
            metadata=metadata
        )
        
        if not result:
            return jsonify({'error': 'Document not found'}), 404
            
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error updating vector document metadata: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/vector-db/collections/<collection_name>/documents/<doc_id>', methods=['DELETE'])
def delete_vector_document(collection_name, doc_id):
    """Delete a document from a vector collection"""
    try:
        if 'vector_db' not in coordinator.tools:
            return jsonify({'error': 'Vector database not available'}), 503
            
        result = coordinator.tools['vector_db'].delete_by_id(collection_name, doc_id)
        if not result:
            return jsonify({'error': 'Document not found'}), 404
            
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error deleting vector document: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# File Manager endpoints
@app.route('/file-manager/preferences', methods=['GET'])
def get_storage_preferences():
    """Get current file storage preferences"""
    try:
        preferences = coordinator.tools['file_manager'].get_storage_preferences()
        return jsonify({'preferences': preferences})
    except Exception as e:
        logger.error(f"Error getting storage preferences: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/file-manager/preferences', methods=['POST'])
def set_storage_preference():
    """Set storage preference for a file type"""
    data = request.get_json()
    file_type = data.get('file_type')
    storage_type = data.get('storage_type')
    
    if not file_type or not storage_type:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        result = coordinator.tools['file_manager'].set_storage_preference(file_type, storage_type)
        if not result:
            return jsonify({'error': 'Invalid storage type or backend not initialized'}), 400
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error setting storage preference: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/file-manager/files', methods=['GET'])
def list_files():
    """List files in a directory"""
    path = request.args.get('path', '')
    storage_type = request.args.get('storage_type')
    file_type = request.args.get('file_type')
    
    try:
        files = coordinator.tools['file_manager'].list_files(path, storage_type, file_type)
        return jsonify({'files': files})
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/file-manager/files', methods=['POST'])
def write_file():
    """Write a file"""
    data = request.get_json()
    path = data.get('path')
    content = data.get('content')
    storage_type = data.get('storage_type')
    file_type = data.get('file_type')
    encoding = data.get('encoding', 'utf-8')
    metadata = data.get('metadata')
    
    if not path or content is None:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        # Determine if we're dealing with text or binary
        if isinstance(content, str):
            result = coordinator.tools['file_manager'].write_text(
                path, content, storage_type, file_type, encoding, metadata
            )
        else:
            # For binary content (would need to be base64 encoded in a real API)
            result = coordinator.tools['file_manager'].write_file(
                path, content, storage_type, file_type, metadata
            )
            
        if not result:
            return jsonify({'error': 'Error writing file'}), 500
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/file-manager/files/<path:file_path>', methods=['GET'])
def read_file(file_path):
    """Read a file"""
    storage_type = request.args.get('storage_type')
    file_type = request.args.get('file_type')
    encoding = request.args.get('encoding', 'utf-8')
    as_text = request.args.get('as_text', 'true').lower() == 'true'
    
    try:
        if as_text:
            content = coordinator.tools['file_manager'].read_text(
                file_path, storage_type, file_type, encoding
            )
            if content is None:
                return jsonify({'error': 'File not found or read error'}), 404
            return jsonify({'content': content})
        else:
            # For binary content, we'd need to handle base64 encoding in a real API
            content = coordinator.tools['file_manager'].read_file(
                file_path, storage_type, file_type
            )
            if content is None:
                return jsonify({'error': 'File not found or read error'}), 404
            return jsonify({'content': 'Binary content', 'size': len(content)})
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/file-manager/files/<path:file_path>', methods=['DELETE'])
def delete_file(file_path):
    """Delete a file"""
    storage_type = request.args.get('storage_type')
    file_type = request.args.get('file_type')
    metadata = request.get_json() if request.is_json else None
    
    try:
        result = coordinator.tools['file_manager'].delete_file(
            file_path, storage_type, file_type, metadata
        )
        if not result:
            return jsonify({'error': 'File not found or delete error'}), 404
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/file-manager/files/<path:file_path>/rename', methods=['POST'])
def rename_file(file_path):
    """Rename a file"""
    data = request.get_json()
    new_path = data.get('new_path')
    storage_type = data.get('storage_type')
    file_type = data.get('file_type')
    metadata = data.get('metadata')
    
    if not new_path:
        return jsonify({'error': 'Missing new_path parameter'}), 400
    
    try:
        result = coordinator.tools['file_manager'].rename_file(
            file_path, new_path, storage_type, file_type, metadata
        )
        if not result:
            return jsonify({'error': 'File not found or rename error'}), 404
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error renaming file: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/file-manager/directories', methods=['POST'])
def create_directory():
    """Create a directory"""
    data = request.get_json()
    path = data.get('path')
    storage_type = data.get('storage_type')
    file_type = data.get('file_type')
    
    if not path:
        return jsonify({'error': 'Missing path parameter'}), 400
    
    try:
        result = coordinator.tools['file_manager'].create_directory(
            path, storage_type, file_type
        )
        if not result:
            return jsonify({'error': 'Error creating directory'}), 500
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error creating directory: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/file-manager/files/<path:file_path>/history', methods=['GET'])
def get_file_history(file_path):
    """Get file history (git only)"""
    max_entries = request.args.get('max_entries', 10, type=int)
    
    try:
        history = coordinator.tools['file_manager'].get_file_history(file_path, max_entries)
        return jsonify({'history': history})
    except Exception as e:
        logger.error(f"Error getting file history: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/file-manager/backends', methods=['POST'])
def initialize_backend():
    """Initialize a storage backend"""
    data = request.get_json()
    backend_type = data.get('backend_type')
    credentials_path = data.get('credentials_path')
    
    if not backend_type or not credentials_path:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        result = coordinator.tools['file_manager'].initialize_backend(
            backend_type, credentials_path=credentials_path
        )
        if not result:
            return jsonify({'error': 'Error initializing backend'}), 500
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error initializing backend: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def api_health():
    """Health check endpoint for the API"""
    return jsonify({
        'status': 'ok',
        'coordinator_available': coordinator is not None,
        'available_features': available_features
    })

if __name__ == '__main__':
    # Configure and initialize the LLM providers based on environment variables
    port = int(os.environ.get('API_PORT', 5000))
    
    # Log the initialization status
    if coordinator is None:
        logger.warning("Starting API server with coordinator unavailable - limited functionality")
        for module, error in available_features.items():
            if isinstance(error, dict):
                for submodule, status in error.items():
                    logger.info(f"  - {module}.{submodule}: {'Available' if status else 'Unavailable'}")
            else:
                logger.info(f"  - {module}: {'Available' if error else 'Unavailable'}")
    else:
        logger.info("Starting API server with full functionality")
        
    app.run(host='0.0.0.0', port=port)