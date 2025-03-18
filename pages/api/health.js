export default function handler(req, res) {
  res.status(200).json({ status: 'ok', message: 'Frontend API is running' });
}