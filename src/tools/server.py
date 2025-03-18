from flask import Flask, request, jsonify
import logging
import os
import sys

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to track available tools/services
available_services = {
    'memory_tool': False,
    'vector_db_tool': False,
    'file_manager': False,
    'structured_data': False,
    'metadata_extractor': False,
    'task_decomposition': False,
    'document_processing': False
}

# Try to initialize each tool with proper error handling
try:
    from src.tools.memory_tool import MemoryTool
    memory = MemoryTool()
    available_services['memory_tool'] = True
    logger.info("Memory tool initialized successfully")
except ImportError as e:
    logger.warning(f"Memory tool could not be initialized: {e}")
except Exception as e:
    logger.error(f"Error initializing Memory tool: {e}")

try:
    from src.tools.vector_db_tool import VectorDBTool
    vector_db = VectorDBTool()
    available_services['vector_db_tool'] = True
    logger.info("Vector DB tool initialized successfully")
except ImportError as e:
    logger.warning(f"Vector DB tool could not be initialized: {e}")
    logger.warning("Missing dependencies: numpy, faiss-cpu, sentence-transformers")
except Exception as e:
    logger.error(f"Error initializing Vector DB tool: {e}")

try:
    from src.tools.file_manager import FileManagerTool
    file_manager = FileManagerTool()
    available_services['file_manager'] = True
    logger.info("File Manager tool initialized successfully")
except ImportError as e:
    logger.warning(f"File Manager tool could not be initialized: {e}")
except Exception as e:
    logger.error(f"Error initializing File Manager tool: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'services': available_services
    })

@app.route('/memory', methods=['GET'])
def memory_status():
    if available_services['memory_tool']:
        try:
            namespaces = memory.list_namespaces()
            return jsonify({
                'status': 'ok',
                'available': True,
                'namespaces': namespaces
            })
        except Exception as e:
            logger.error(f"Error getting memory status: {e}")
            return jsonify({
                'status': 'error',
                'available': True,
                'error': str(e)
            })
    else:
        return jsonify({
            'status': 'unavailable',
            'available': False,
            'message': 'Memory tool is not available'
        })

@app.route('/vector-db', methods=['GET'])
def vector_db_status():
    if available_services['vector_db_tool']:
        try:
            collections = vector_db.list_collections()
            return jsonify({
                'status': 'ok',
                'available': True,
                'collections': collections
            })
        except Exception as e:
            logger.error(f"Error getting vector DB status: {e}")
            return jsonify({
                'status': 'error',
                'available': True,
                'error': str(e)
            })
    else:
        return jsonify({
            'status': 'unavailable',
            'available': False,
            'message': 'Vector DB tool is not available'
        })

@app.route('/file-manager', methods=['GET'])
def file_manager_status():
    if available_services['file_manager']:
        try:
            preferences = file_manager.get_storage_preferences()
            return jsonify({
                'status': 'ok',
                'available': True,
                'preferences': preferences
            })
        except Exception as e:
            logger.error(f"Error getting file manager status: {e}")
            return jsonify({
                'status': 'error',
                'available': True,
                'error': str(e)
            })
    else:
        return jsonify({
            'status': 'unavailable',
            'available': False,
            'message': 'File Manager tool is not available'
        })

if __name__ == '__main__':
    port = int(os.environ.get('TOOLS_PORT', 5001))
    app.run(host='0.0.0.0', port=port)