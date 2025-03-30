"""
API Integration Tool for OpenManus.

This tool provides a unified interface for interacting with various external APIs,
including media downloading, data retrieval, and specialized service integrations.
"""

import os
import json
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path

from src.tools.api_integrations import (
    APIIntegrationManager,
    APIIntegrationError,
    APISubscriptionError,
    APIKeyError
)

# Set up logging
logger = logging.getLogger(__name__)

class APIIntegrationTool:
    """
    Tool for integrating with external APIs.
    
    This tool provides a unified interface for working with various
    third-party APIs like RapidAPI services and Google Cloud APIs.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the API integration tool.
        
        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        
        # Set up the base paths
        self.base_path = Path(self.config.get("base_path", "data/api_cache"))
        self.download_path = Path(self.config.get("download_path", "data/downloads"))
        
        # Create directories if they don't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize the API integration manager
        manager_config = self.config.get("api_manager", {})
        manager_config["cache_dir"] = str(self.base_path)
        self.api_manager = APIIntegrationManager(manager_config)
        
        # Register notification handler
        self.api_manager.register_notification_callback(self._handle_notification)
        
        # Track requests that need user attention
        self.pending_activations = {}
    
    def _handle_notification(self, message: str, metadata: Dict[str, Any]) -> None:
        """
        Handle notifications from the API manager.
        
        Args:
            message: The notification message.
            metadata: Additional metadata for the notification.
        """
        # Log the notification
        logger.warning(f"API Notification: {message}")
        
        # Store pending activation requests
        if "subscription" in message.lower() or "activation" in message.lower():
            request_id = metadata.get("request_id", f"request_{len(self.pending_activations) + 1}")
            self.pending_activations[request_id] = {
                "message": message,
                "metadata": metadata,
                "timestamp": metadata.get("timestamp", 0),
                "status": "pending"
            }
            
            # Log that user action is required
            logger.warning(f"User action required: {message} (Request ID: {request_id})")
    
    def download_media(self, url: str, output_path: Optional[str] = None, 
                       options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Download media from a URL.
        
        Args:
            url: The URL of the media to download.
            output_path: Optional path to save the downloaded media.
            options: Additional options for the download.
            
        Returns:
            Dictionary with information about the downloaded media.
        """
        options = options or {}
        
        try:
            # Download via API manager
            result = self.api_manager.download_media(url, options)
            
            # If output_path is specified, copy the file there
            if output_path and result.get("success", False):
                downloaded_file = result.get("download", {}).get("filepath")
                if downloaded_file and os.path.exists(downloaded_file):
                    # Create output directory if it doesn't exist
                    output_dir = os.path.dirname(output_path)
                    if output_dir:
                        os.makedirs(output_dir, exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(downloaded_file, output_path)
                    result["download"]["output_path"] = output_path
            
            return result
        except APISubscriptionError as e:
            logger.warning(f"API subscription error: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "requires_activation": True,
                "action_required": "Please activate the required API subscription and try again."
            }
        except APIKeyError as e:
            logger.warning(f"API key error: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "requires_api_key": True,
                "action_required": "Please provide the required API key and try again."
            }
        except APIIntegrationError as e:
            logger.error(f"API integration error: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "url": url
            }
    
    def get_available_apis(self) -> Dict[str, Any]:
        """
        Get information about available APIs.
        
        Returns:
            Dictionary with information about available APIs.
        """
        try:
            apis = self.api_manager.get_available_apis()
            return {
                "success": True,
                "providers": apis,
                "pending_activations": self.pending_activations,
                "status": "available" if apis else "no_apis_configured"
            }
        except Exception as e:
            logger.error(f"Error getting available APIs: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    def check_activation_status(self, request_id: str) -> Dict[str, Any]:
        """
        Check the status of an API activation request.
        
        Args:
            request_id: The ID of the activation request to check.
            
        Returns:
            Dictionary with the status of the activation request.
        """
        if request_id not in self.pending_activations:
            return {
                "success": False,
                "error": f"No activation request found with ID: {request_id}",
                "status": "not_found"
            }
        
        activation = self.pending_activations[request_id]
        
        # In a real implementation, this would check the actual status
        # For now, we'll just return the stored status
        return {
            "success": True,
            "status": activation["status"],
            "message": activation["message"],
            "metadata": activation["metadata"]
        }
    
    def confirm_activation(self, request_id: str) -> Dict[str, Any]:
        """
        Confirm that an API activation has been completed.
        
        Args:
            request_id: The ID of the activation request to confirm.
            
        Returns:
            Dictionary with the result of the confirmation.
        """
        if request_id not in self.pending_activations:
            return {
                "success": False,
                "error": f"No activation request found with ID: {request_id}",
                "status": "not_found"
            }
        
        # Update the status
        self.pending_activations[request_id]["status"] = "confirmed"
        
        # In a real implementation, this would refresh the API manager to use the new activation
        # For now, we'll just log it
        logger.info(f"API activation confirmed for request ID: {request_id}")
        
        return {
            "success": True,
            "message": f"API activation confirmed for request ID: {request_id}",
            "status": "confirmed"
        }
    
    def extract_media_info(self, url: str) -> Dict[str, Any]:
        """
        Extract information about media without downloading it.
        
        Args:
            url: The URL of the media to analyze.
            
        Returns:
            Dictionary with information about the media.
        """
        try:
            # This uses the same underlying API as download_media, but doesn't save the file
            result = self.api_manager.download_media(url, {"info_only": True})
            
            if not result.get("success", False):
                return result
            
            # Filter out download information to just return metadata
            if "download" in result:
                del result["download"]
            
            return result
        except Exception as e:
            logger.error(f"Error extracting media info: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def search_api(self, provider: str, api_id: str, query: str, 
                   options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a search using an API.
        
        Args:
            provider: The provider to use (e.g., "rapidapi", "google").
            api_id: The ID of the specific API to use.
            query: The search query.
            options: Additional options for the search.
            
        Returns:
            Dictionary with search results.
        """
        # This is a placeholder implementation
        # In a real implementation, this would use the API manager to perform the search
        logger.info(f"Searching {provider}/{api_id} for: {query}")
        
        return {
            "success": True,
            "provider": provider,
            "api": api_id,
            "query": query,
            "results": [
                {"title": f"Result 1 for {query}", "url": f"https://example.com/result1"},
                {"title": f"Result 2 for {query}", "url": f"https://example.com/result2"}
            ],
            "message": "This is a placeholder implementation"
        }