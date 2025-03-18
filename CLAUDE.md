# OpenManus Development Guide

## Commands
- Build: `npm run build` (Next.js frontend)
- Lint: `npm run lint` (Next.js frontend)
- Dev server: `npm run dev` (Next.js frontend)
- Run backend: `python src/server.py`
- Docker: `docker-compose up` (all services), `docker-compose build` (rebuild)

## Code Style

### Python
- **Imports:** Standard lib → third-party → local (alphabetical)
- **Type Hints:** Use typing module (Dict, List, Optional, Any)
- **Classes:** PascalCase with docstrings, @abstractmethod where appropriate
- **Functions:** snake_case with docstrings for public methods
- **Error Handling:** Use specific exceptions, log errors appropriately
- **Structure:** Class-based architecture with coordinator pattern

### JavaScript/React
- **Components:** PascalCase functional components
- **File Structure:** Follow Next.js conventions
- **State Management:** React hooks (useState, useEffect)
- **API Calls:** Axios for network requests

## Architecture
OpenManus is a multi-agent system with plugin tools and LLM service that supports multiple providers (OpenAI, Claude, local models).

## Configuration

### File Storage Configuration
To enable or disable specific file storage backends (local, Google Drive, OneDrive, Git):

1. Edit the `file_manager_config.json` file:
   ```json
   {
     "backends": {
       "local": {
         "enabled": true,
         "base_path": "data/files/local",
         "requires_auth": false
       },
       "git": {
         "enabled": true,
         "base_path": "data/files/git",
         "requires_auth": false,
         "user_name": "OpenManus",
         "user_email": "openmanus@example.com"
       },
       "google_drive": {
         "enabled": true,
         "requires_auth": true,
         "credentials_path": "credentials/google_drive_credentials.json",
         "root_folder": "OpenManus"
       },
       "onedrive": {
         "enabled": false,
         "requires_auth": true,
         "credentials_path": "credentials/onedrive_credentials.json",
         "root_folder": "OpenManus"
       }
     },
     "storage_preferences": {
       "temp": "local",
       "code": "git",
       "knowledge": "git",
       "document": "google_drive",
       "image": "google_drive",
       "video": "google_drive",
       "audio": "google_drive",
       "general": "local"
     }
   }
   ```

2. Set `"enabled": true` or `"enabled": false` for each backend you want to use or disable
3. Configure the storage preferences to determine which backend is used for each file type
4. For authenticated backends (Google Drive, OneDrive), provide the credentials files in the specified paths