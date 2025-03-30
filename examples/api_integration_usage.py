#!/usr/bin/env python3
"""
Example script demonstrating the use of the API Integration Tool in OpenManus.
This script shows how to use external APIs like RapidAPI and Google API,
and how to handle subscription activation workflows.
"""

import sys
import os
import json
from pprint import pprint

# Add the parent directory to sys.path to import OpenManus modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.tools.api_integration_tool import APIIntegrationTool
    from src.tools.api_integrations import APIIntegrationError
except ImportError as e:
    print(f"Error importing API Integration Tool: {e}")
    print("Please install the required dependencies.")
    sys.exit(1)

def print_section(title):
    """Helper to print formatted section titles"""
    print(f"\n{title}")
    print("=" * len(title))

def format_result(result):
    """Helper to format API results for display"""
    try:
        return json.dumps(result, indent=2)
    except:
        return str(result)

def main():
    print("OpenManus API Integration Demo")
    print("=" * 60)
    
    # Create API Integration Tool
    api_tool = APIIntegrationTool()
    print("API Integration Tool initialized")
    
    # Section 1: List available APIs
    print_section("1. Available APIs")
    
    try:
        apis = api_tool.get_available_apis()
        
        if not apis.get("success", False):
            print(f"Error: {apis.get('error', 'Unknown error')}")
        else:
            providers = apis.get("providers", {})
            if not providers:
                print("No API providers available")
                print("You need to set API keys in environment variables:")
                print("  RAPIDAPI_KEY=your_key_here")
                print("  GOOGLE_API_KEY=your_key_here")
            else:
                print("Available API providers:")
                for provider, available_apis in providers.items():
                    print(f"\n{provider.upper()}:")
                    for api in available_apis:
                        print(f"  - {api.get('name', 'Unknown')}: {api.get('description', 'No description')}")
                        if "endpoints" in api:
                            print(f"    Endpoints: {', '.join(api['endpoints'])}")
    except Exception as e:
        print(f"Error listing APIs: {e}")
    
    # Section 2: Using RapidAPI for social media
    print_section("2. Social Media Content Analysis")
    
    # Example URLs for various platforms
    example_urls = [
        "https://twitter.com/OpenAI/status/1234567890",
        "https://www.instagram.com/p/abcdefghijk/",
        "https://www.threads.net/@aaron.rupar/post/DHwUgjvpJyh",
        "https://www.tiktok.com/@tiktok/video/1234567890",
    ]
    
    for url in example_urls:
        print(f"\nAnalyzing: {url}")
        try:
            # Extract information about the media without downloading
            info = api_tool.extract_media_info(url)
            
            if not info.get("success", False):
                if info.get("requires_activation", False):
                    print(f"API activation required: {info.get('action_required', '')}")
                    # In a real application, this would trigger the activation workflow
                    print(f"To simulate activation, you would implement:")
                    print(f"1. Get activation requirements")
                    print(f"2. Notify user and wait for confirmation")
                    print(f"3. Resume workflow after activation")
                elif info.get("requires_api_key", False):
                    print(f"API key required: {info.get('action_required', '')}")
                else:
                    print(f"Error: {info.get('error', 'Unknown error')}")
            else:
                # In a real application, this would return actual data
                print(f"Platform: {info.get('platform', 'unknown')}")
                print(f"Media Type: {info.get('media_type', 'unknown')}")
                print(f"Author: {info.get('author', {}).get('name', 'unknown')}")
                print(f"Title: {info.get('title', 'unknown')}")
                if "metadata" in info:
                    metadata = info["metadata"]
                    print(f"Duration: {metadata.get('duration', 'unknown')} seconds")
                    print(f"Created: {metadata.get('created_at', 'unknown')}")
                    print(f"Engagement: {metadata.get('views', 0)} views, {metadata.get('likes', 0)} likes")
        except Exception as e:
            print(f"Error analyzing URL: {e}")
    
    # Section 3: Download Media (Simulated)
    print_section("3. Media Download (Simulated)")
    
    example_video_url = "https://www.threads.net/@aaron.rupar/post/DHwUgjvpJyh"
    print(f"Downloading media from: {example_video_url}")
    
    try:
        # Try to download the media
        download_result = api_tool.download_media(
            url=example_video_url,
            output_path="/tmp/downloaded_video.mp4"
        )
        
        if not download_result.get("success", False):
            if download_result.get("requires_activation", False):
                print(f"API activation required: {download_result.get('action_required', '')}")
                
                # This would be a request_id in a real scenario
                request_id = "sample_request_1"
                
                print("\nSimulating activation workflow:")
                print("1. Check activation status")
                status = api_tool.check_activation_status(request_id)
                print(f"   Status: {status.get('status', 'unknown')}")
                
                print("2. User activates the subscription (external step)")
                print("3. Confirm activation")
                confirmation = api_tool.confirm_activation(request_id)
                print(f"   Confirmation: {confirmation.get('message', '')}")
                
                print("4. Retry download after activation")
                # We'd retry the download here after activation
            else:
                print(f"Error: {download_result.get('error', 'Unknown error')}")
        else:
            # In a real scenario, we'd have actual download information
            print(f"Download successful!")
            print(f"Media URL: {download_result.get('media_url', 'unknown')}")
            if "download" in download_result:
                download_info = download_result["download"]
                print(f"Saved to: {download_info.get('output_path', download_info.get('filepath', 'unknown'))}")
                print(f"File size: {download_info.get('size', 0)} bytes")
    except Exception as e:
        print(f"Error downloading media: {e}")
    
    # Section 4: Search API (Simulated)
    print_section("4. API Search (Simulated)")
    
    try:
        # Example of searching using Google API
        search_result = api_tool.search_api(
            provider="google",
            api_id="youtube",
            query="OpenManus AI agent framework",
            options={"max_results": 5}
        )
        
        if not search_result.get("success", False):
            print(f"Error: {search_result.get('error', 'Unknown error')}")
        else:
            # This would show real search results in actual implementation
            print(f"Search results from {search_result.get('provider')}/{search_result.get('api')}:")
            for i, result in enumerate(search_result.get("results", []), 1):
                print(f"{i}. {result.get('title', 'Unknown')} - {result.get('url', 'Unknown URL')}")
    except Exception as e:
        print(f"Error searching API: {e}")
    
    print("\nAPI Integration demo complete!")
    print("=" * 60)
    print("Note: This demo uses placeholder implementations. In a real environment,")
    print("the API integrations would make actual API calls to external services.")

if __name__ == "__main__":
    main()