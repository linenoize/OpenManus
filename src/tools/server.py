from flask import Flask, request, jsonify
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('TOOLS_PORT', 5001))
    app.run(host='0.0.0.0', port=port)