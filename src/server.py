from flask import Flask, request, jsonify
from agents.coordinator import TaskCoordinator
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
coordinator = TaskCoordinator()

@app.route('/task', methods=['POST'])
def submit_task():
    data = request.get_json()
    task = data.get('task')
    if not task:
        return jsonify({'error': 'No task provided'}), 400
    
    result = coordinator.execute_task(task)
    return jsonify(result)

@app.route('/status', methods=['GET'])
def get_status():
    # Check if any LLM providers are configured
    llm_providers = coordinator.llm_service.list_providers()
    providers_info = [p["name"] for p in llm_providers]
    
    return jsonify({
        'status': 'running',
        'llm_providers': providers_info
    })

@app.route('/llm/providers', methods=['GET'])
def get_llm_providers():
    """Get all available LLM providers with capabilities"""
    providers = coordinator.llm_service.list_providers()
    return jsonify({'providers': providers})

@app.route('/llm/recommendations', methods=['GET'])
def get_llm_recommendations():
    """Get current LLM recommendations for agents and tools"""
    recommendations = coordinator.get_provider_recommendations()
    return jsonify(recommendations)

@app.route('/llm/preference', methods=['POST'])
def set_llm_preference():
    """Set LLM preference for a specific agent or tool"""
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
    try:
        namespaces = coordinator.tools['memory'].list_namespaces()
        return jsonify({'namespaces': namespaces})
    except Exception as e:
        logger.error(f"Error listing memory namespaces: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/memory/<namespace>', methods=['GET'])
def get_memories(namespace):
    """Get all memories in a namespace"""
    try:
        memories = coordinator.tools['memory'].get_all(namespace)
        return jsonify({'memories': memories})
    except Exception as e:
        logger.error(f"Error getting memories: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/memory/<namespace>/search', methods=['GET'])
def search_memories(namespace):
    """Search memories in a namespace"""
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        results = coordinator.tools['memory'].search(query, namespace)
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/memory/<namespace>', methods=['POST'])
def store_memory(namespace):
    """Store a memory in a namespace"""
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
        return jsonify({'error': 'Internal server error'}), 500

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

if __name__ == '__main__':
    # Configure and initialize the LLM providers based on environment variables
    app.run(host='0.0.0.0', port=5000)