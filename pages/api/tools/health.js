export default function handler(req, res) {
  res.status(200).json({ 
    status: 'ok', 
    message: 'Tools service is available through the frontend API proxy',
    tools: [
      { name: 'file_manager', status: 'available', version: '0.1.0' },
      { name: 'llm_service', status: 'available', version: '0.1.0' },
      { name: 'memory_tool', status: 'available', version: '0.1.0' },
      { name: 'vector_db', status: 'available', version: '0.1.0' },
      { name: 'code_executor', status: 'available', version: '0.1.0' }
    ]
  });
}