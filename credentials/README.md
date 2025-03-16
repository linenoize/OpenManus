# OpenManus Storage Credentials

This directory contains credential files for cloud storage providers.

## Google Drive Setup

To use the Google Drive storage backend:

1. **Create a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Drive API for this project

2. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Give it a name (e.g., "OpenManus File Manager")
   - Click "Create"

3. **Download Credentials**:
   - Download the JSON file
   - Rename it to `google_drive_credentials.json`
   - Place it in this directory

4. **First Run**:
   - The first time you use the Google Drive backend, it will launch a browser window for authentication
   - Log in to your Google account and grant the requested permissions
   - After successful authentication, a token will be saved for future use

## OneDrive Setup

To use the OneDrive storage backend:

> **Note**: The OneDrive backend is currently a placeholder and not fully implemented.

1. **Register an App in the Microsoft App Registration Portal**:
   - Go to the [Microsoft App Registration Portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
   - Click "New registration"
   - Name your app (e.g., "OpenManus File Manager")
   - Select "Accounts in any organizational directory and personal Microsoft accounts"
   - For Redirect URI, select "Public client/native" and enter `http://localhost:8000`
   - Click "Register"

2. **Add Microsoft Graph Permissions**:
   - Go to "API permissions"
   - Click "Add a permission"
   - Select "Microsoft Graph" > "Delegated permissions"
   - Add the following permissions:
     - Files.ReadWrite
     - Files.ReadWrite.All
     - User.Read
   - Click "Add permissions"

3. **Create a Credentials File**:
   - Create a file named `onedrive_credentials.json` in this directory
   - Add the following content, replacing the placeholder values:

```json
{
  "client_id": "YOUR_CLIENT_ID",
  "tenant_id": "common"
}
```

## Security Note

- These credential files contain sensitive information and should not be committed to version control
- The `.gitignore` file is configured to exclude this directory, but always double-check before committing
- If you need to share these credentials with other developers, use a secure method (not email or chat)