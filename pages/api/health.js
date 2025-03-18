export default function handler(req, res) {
  res.status(200).json({ 
    status: 'ok', 
    message: 'Frontend API is running',
    services: {
      api: 'online',
      tools: 'offline',
      fileManager: 'offline',
      vectorDb: 'offline',
      llmService: 'offline'
    },
    environment: {
      nodeEnv: process.env.NODE_ENV,
      version: '0.1.0'
    }
  });
}