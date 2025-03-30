"""
Base classes for API integration in OpenManus.

This module provides the core framework for integrating with external APIs,
including API key management, error handling, and subscription status checking.
"""

import os
import json
import time
import logging
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Union, Callable

# Set up logging
logger = logging.getLogger(__name__)

class APIIntegrationError(Exception):
    """Base exception for API integration errors."""
    pass

class APIKeyError(APIIntegrationError):
    """Exception raised when there is an issue with API keys."""
    pass

class APISubscriptionError(APIIntegrationError):
    """Exception raised when there is an issue with API subscriptions."""
    pass

class BaseAPIProvider(ABC):
    """Abstract base class for API providers."""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the API provider.
        
        Args:
            api_key: Optional API key. If not provided, will check environment variables.
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.api_key = api_key
        self._validate_credentials()
        
        # Track usage for rate limiting and subscription status
        self.usage_stats = {
            "requests": 0,
            "last_request_time": 0,
            "error_count": 0,
            "subscription_checked": False,
            "subscription_status": None
        }
    
    @abstractmethod
    def _validate_credentials(self) -> None:
        """Validate API credentials."""
        pass
    
    @abstractmethod
    def check_subscription_status(self) -> Dict[str, Any]:
        """
        Check the status of the API subscription.
        
        Returns:
            Dictionary with subscription status information.
        """
        pass
    
    @abstractmethod
    def get_available_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get a list of available API endpoints.
        
        Returns:
            List of dictionaries containing endpoint information.
        """
        pass
    
    def update_usage_stats(self, success: bool = True) -> None:
        """
        Update usage statistics.
        
        Args:
            success: Whether the API request was successful.
        """
        current_time = time.time()
        self.usage_stats["requests"] += 1
        self.usage_stats["last_request_time"] = current_time
        
        if not success:
            self.usage_stats["error_count"] += 1
    
    def should_check_subscription(self) -> bool:
        """
        Determine if subscription status should be checked.
        
        Returns:
            True if subscription status should be checked, False otherwise.
        """
        # Check subscription status if not checked before
        if not self.usage_stats["subscription_checked"]:
            return True
            
        # Check again if there have been errors since last check
        if self.usage_stats["error_count"] > 0:
            return True
            
        # Otherwise, check once every 24 hours (86400 seconds)
        current_time = time.time()
        last_check_time = self.usage_stats.get("last_subscription_check", 0)
        return (current_time - last_check_time) > 86400
    
    def log_subscription_check(self, status: Dict[str, Any]) -> None:
        """
        Log a subscription status check.
        
        Args:
            status: Dictionary with subscription status information.
        """
        self.usage_stats["subscription_checked"] = True
        self.usage_stats["subscription_status"] = status
        self.usage_stats["last_subscription_check"] = time.time()
        self.usage_stats["error_count"] = 0


class RapidAPIProvider(BaseAPIProvider):
    """Provider for RapidAPI services."""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the RapidAPI provider.
        
        Args:
            api_key: RapidAPI key. If not provided, will check RAPIDAPI_KEY environment variable.
            config: Optional configuration dictionary.
        """
        self.api_key = api_key or os.environ.get("RAPIDAPI_KEY")
        super().__init__(self.api_key, config)
        self.base_url = "https://rapidapi.com/connect/api"
        self.available_apis = {}
        self.cache_dir = config.get("cache_dir", "data/api_cache/rapidapi")
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _validate_credentials(self) -> None:
        """Validate RapidAPI credentials."""
        if not self.api_key:
            logger.warning("RapidAPI key not found. Set RAPIDAPI_KEY environment variable or provide api_key parameter.")
            raise APIKeyError("RapidAPI key not found")
    
    def check_subscription_status(self) -> Dict[str, Any]:
        """
        Check the status of RapidAPI subscriptions.
        
        Returns:
            Dictionary with subscription status information.
        """
        # In a real implementation, this would make an API call to RapidAPI to check subscription status
        # For now, we'll return a placeholder
        status = {
            "active": True,
            "remaining_requests": 1000,
            "subscribed_apis": [
                {"id": "social-download-all-in-one", "name": "Social Download All in One", "active": True},
                {"id": "google-search3", "name": "Google Search API", "active": True}
            ],
            "rate_limits": {
                "requests_per_day": 1000,
                "requests_per_minute": 60
            }
        }
        
        self.log_subscription_check(status)
        return status
        
    def get_available_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get a list of available RapidAPI endpoints.
        
        Returns:
            List of dictionaries containing endpoint information.
        """
        # For now, we'll return a placeholder list of example endpoints
        return [
            {
                "id": "social-download-all-in-one",
                "name": "Social Download All in One",
                "description": "Download media from social platforms",
                "endpoints": ["download", "info"],
                "platforms": ["twitter", "instagram", "threads", "tiktok", "facebook"]
            },
            {
                "id": "google-search3",
                "name": "Google Search API",
                "description": "Get Google search results",
                "endpoints": ["search", "news", "images"],
                "parameters": ["query", "limit", "lang"]
            }
        ]
    
    def download_media(self, url: str, platform: Optional[str] = None) -> Dict[str, Any]:
        """
        Download media from a social media platform.
        
        Args:
            url: URL of the content to download.
            platform: Optional platform name (auto-detected if not provided).
            
        Returns:
            Dictionary with download information.
        """
        if self.should_check_subscription():
            status = self.check_subscription_status()
            if not status["active"]:
                raise APISubscriptionError(f"RapidAPI subscription not active")
        
        # Check if we've already downloaded this URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{url_hash}.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                logger.info(f"Retrieved media info from cache for {url}")
                return cache_data
        
        # In a real implementation, this would make an API call to RapidAPI
        # For now, we'll return a placeholder response
        logger.info(f"Downloading media from {url} via RapidAPI")
        
        # Simulate platform detection
        if not platform:
            if "twitter.com" in url or "x.com" in url:
                platform = "twitter"
            elif "instagram.com" in url:
                platform = "instagram"
            elif "threads.net" in url:
                platform = "threads"
            elif "tiktok.com" in url:
                platform = "tiktok"
            elif "facebook.com" in url:
                platform = "facebook"
            else:
                platform = "unknown"
        
        result = {
            "success": True,
            "platform": platform,
            "url": url,
            "media_type": "video" if "video" in url or platform in ["tiktok", "threads"] else "image",
            "media_url": f"https://example.com/media/{platform}/{url_hash}.mp4",
            "thumbnail_url": f"https://example.com/thumbnails/{platform}/{url_hash}.jpg",
            "title": f"Sample {platform} content",
            "description": f"This is a placeholder description for {platform} content at {url}",
            "author": {
                "name": "Sample Author",
                "profile_url": f"https://{platform}.com/sampleauthor"
            },
            "metadata": {
                "duration": 120 if platform in ["tiktok", "threads", "twitter"] else None,
                "width": 1280,
                "height": 720,
                "created_at": "2023-01-01T00:00:00Z",
                "views": 1000,
                "likes": 500,
                "comments": 100
            },
            "download": {
                "status": "success",
                "filepath": f"/tmp/{url_hash}.mp4",
                "size": 1024000
            }
        }
        
        # Cache the result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        self.update_usage_stats(True)
        return result


class GoogleAPIProvider(BaseAPIProvider):
    """Provider for Google Cloud APIs."""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Google API provider.
        
        Args:
            api_key: Google API key. If not provided, will check GOOGLE_API_KEY environment variable.
            config: Optional configuration dictionary.
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        super().__init__(self.api_key, config)
        self.available_apis = {}
        
    def _validate_credentials(self) -> None:
        """Validate Google API credentials."""
        if not self.api_key:
            logger.warning("Google API key not found. Set GOOGLE_API_KEY environment variable or provide api_key parameter.")
            raise APIKeyError("Google API key not found")
    
    def check_subscription_status(self) -> Dict[str, Any]:
        """
        Check the status of Google API subscriptions.
        
        Returns:
            Dictionary with subscription status information.
        """
        # In a real implementation, this would make an API call to Google Cloud to check subscription status
        # For now, we'll return a placeholder
        status = {
            "active": True,
            "enabled_apis": [
                {"id": "youtube", "name": "YouTube Data API", "active": True},
                {"id": "vision", "name": "Cloud Vision API", "active": True},
                {"id": "speech", "name": "Speech-to-Text API", "active": True}
            ],
            "quota": {
                "youtube": {"daily_limit": 10000, "remaining": 9900},
                "vision": {"daily_limit": 1000, "remaining": 950},
                "speech": {"daily_limit": 60, "remaining": 60}
            }
        }
        
        self.log_subscription_check(status)
        return status
        
    def get_available_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get a list of available Google API endpoints.
        
        Returns:
            List of dictionaries containing endpoint information.
        """
        # For now, we'll return a placeholder list
        return [
            {
                "id": "youtube",
                "name": "YouTube Data API",
                "description": "Access YouTube data including videos, channels, and playlists",
                "endpoints": ["videos.list", "search.list", "channels.list"]
            },
            {
                "id": "vision",
                "name": "Cloud Vision API",
                "description": "Integrate vision detection features including image labeling, face and landmark detection, OCR",
                "endpoints": ["annotate", "detect", "ocr"]
            },
            {
                "id": "speech",
                "name": "Speech-to-Text API",
                "description": "Convert audio to text using Google's speech recognition technology",
                "endpoints": ["recognize", "longRunningRecognize"]
            }
        ]


class APIIntegrationManager:
    """
    Manager for API integrations.
    
    This class manages multiple API providers and handles initialization,
    error recovery, and fallback logic.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the API integration manager.
        
        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.providers = {}
        self.initialized = False
        self.notification_callbacks = []
        self.cache_dir = self.config.get("cache_dir", "data/api_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize API providers based on available credentials."""
        # Initialize RapidAPI if key is available
        try:
            if os.environ.get("RAPIDAPI_KEY") or self.config.get("rapidapi_key"):
                api_key = self.config.get("rapidapi_key") or os.environ.get("RAPIDAPI_KEY")
                provider_config = self.config.get("rapidapi_config", {})
                provider_config["cache_dir"] = os.path.join(self.cache_dir, "rapidapi")
                
                self.providers["rapidapi"] = RapidAPIProvider(api_key, provider_config)
                logger.info("RapidAPI provider initialized successfully")
        except APIKeyError:
            logger.warning("RapidAPI provider not initialized: API key missing")
        except Exception as e:
            logger.error(f"Failed to initialize RapidAPI provider: {e}")
        
        # Initialize Google API if key is available
        try:
            if os.environ.get("GOOGLE_API_KEY") or self.config.get("google_api_key"):
                api_key = self.config.get("google_api_key") or os.environ.get("GOOGLE_API_KEY")
                provider_config = self.config.get("google_api_config", {})
                
                self.providers["google"] = GoogleAPIProvider(api_key, provider_config)
                logger.info("Google API provider initialized successfully")
        except APIKeyError:
            logger.warning("Google API provider not initialized: API key missing")
        except Exception as e:
            logger.error(f"Failed to initialize Google API provider: {e}")
            
        self.initialized = len(self.providers) > 0
        if not self.initialized:
            logger.warning("No API providers initialized. Set API keys via environment variables or configuration.")
    
    def register_notification_callback(self, callback: Callable) -> None:
        """
        Register a callback for API activation notifications.
        
        Args:
            callback: A callable that accepts a notification message and metadata.
        """
        self.notification_callbacks.append(callback)
    
    def notify(self, message: str, metadata: Dict[str, Any]) -> None:
        """
        Send a notification to all registered callbacks.
        
        Args:
            message: The notification message.
            metadata: Additional metadata for the notification.
        """
        for callback in self.notification_callbacks:
            try:
                callback(message, metadata)
            except Exception as e:
                logger.error(f"Error in notification callback: {e}")
    
    def download_media(self, url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Download media from a URL using available providers.
        
        Args:
            url: The URL of the media to download.
            options: Optional parameters for the download.
            
        Returns:
            Dictionary with download information.
        """
        options = options or {}
        platform = options.get("platform")
        
        if not self.initialized:
            raise APIIntegrationError("No API providers initialized. Please set API keys.")
        
        # Try RapidAPI first for social media
        if "rapidapi" in self.providers:
            try:
                provider = self.providers["rapidapi"]
                if provider.should_check_subscription():
                    status = provider.check_subscription_status()
                    if not status.get("active", False):
                        self.notify(
                            "RapidAPI subscription inactive. Please activate it to download media.",
                            {"provider": "rapidapi", "url": url, "status": status}
                        )
                        raise APISubscriptionError("RapidAPI subscription not active")
                
                return provider.download_media(url, platform)
            except APISubscriptionError as e:
                logger.warning(f"RapidAPI subscription error: {e}")
                # Try fallback if available
                if "google" in self.providers:
                    logger.info(f"Falling back to Google API for media download: {url}")
                    # Call equivalent Google API method here
            except Exception as e:
                logger.error(f"Error downloading media via RapidAPI: {e}")
        
        # Fallback to direct download if no API available
        logger.warning(f"No suitable API provider for media download: {url}")
        return {
            "success": False,
            "error": "No suitable API provider available",
            "url": url,
            "fallback": "direct_download"
        }
    
    def get_available_apis(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get a dictionary of available APIs from all providers.
        
        Returns:
            Dictionary mapping provider names to lists of available APIs.
        """
        result = {}
        
        for provider_name, provider in self.providers.items():
            try:
                if provider.should_check_subscription():
                    provider.check_subscription_status()
                result[provider_name] = provider.get_available_endpoints()
            except Exception as e:
                logger.error(f"Error getting available APIs for {provider_name}: {e}")
                result[provider_name] = [{"error": str(e)}]
        
        return result