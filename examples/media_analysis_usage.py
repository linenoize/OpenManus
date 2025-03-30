#!/usr/bin/env python3
"""
Example script demonstrating the use of the Media Analysis Tool in OpenManus.
This script shows how to analyze various media types including images, videos, and audio.
"""

import sys
import os
import json
from pprint import pprint

# Add the parent directory to sys.path to import OpenManus modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.tools.media_analysis_tool import MediaAnalysisTool
    from src.tools.api_integration_tool import APIIntegrationTool
except ImportError as e:
    print(f"Error importing Media Analysis Tool: {e}")
    print("Please install the required dependencies.")
    sys.exit(1)

def print_section(title):
    """Helper to print formatted section titles"""
    print(f"\n{title}")
    print("=" * len(title))

def format_result(result):
    """Format complex results for display by selectively showing important parts"""
    if not isinstance(result, dict):
        return str(result)
    
    # Create a simplified version of the result for display
    display_result = {}
    
    # Always include success status and any errors
    display_result["success"] = result.get("success", False)
    if not result.get("success", False) and "error" in result:
        display_result["error"] = result["error"]
        return json.dumps(display_result, indent=2)
    
    # Include basic information
    for key in ["media_path", "media_type", "analysis_type", "extraction_type", "is_url"]:
        if key in result:
            display_result[key] = result[key]
    
    # Include verification score and confidence if available
    for key in ["verification_score", "confidence"]:
        if key in result:
            display_result[key] = result[key]
    
    # Include metadata summary if available
    if "metadata" in result:
        metadata = result["metadata"]
        display_result["metadata"] = {
            "duration": metadata.get("duration", 0) if "duration" in metadata else None,
            "dimensions": f"{metadata.get('width', 0)}x{metadata.get('height', 0)}" 
                if "width" in metadata and "height" in metadata else None,
            "format": metadata.get("format", ""),
            "size": metadata.get("size", 0)
        }
        # Remove None values
        display_result["metadata"] = {k: v for k, v in display_result["metadata"].items() if v is not None}
    
    # Include content summary based on media type
    if "content" in result:
        content = result["content"]
        content_summary = {}
        
        # For image analysis
        if "labels" in content:
            content_summary["labels"] = [label["description"] for label in content["labels"][:3]] if content["labels"] else []
            content_summary["label_count"] = len(content["labels"])
        
        if "objects" in content:
            content_summary["object_count"] = len(content["objects"])
            if content["objects"]:
                content_summary["object_examples"] = [obj["name"] for obj in content["objects"][:3]]
        
        if "faces" in content:
            content_summary["face_count"] = len(content["faces"])
        
        # For video analysis
        if "scenes" in content:
            content_summary["scene_count"] = len(content["scenes"])
        
        if "key_frames" in content:
            content_summary["keyframe_count"] = len(content["key_frames"])
        
        # For audio/transcript
        if "transcript" in content:
            if content["transcript"]:
                # Just include a preview of the transcript
                transcript_preview = content["transcript"].strip().split("\n")[:3]
                content_summary["transcript_preview"] = "\n".join(transcript_preview)
                content_summary["full_transcript_length"] = len(content["transcript"])
        
        if "speakers" in content:
            content_summary["speaker_count"] = len(content["speakers"])
        
        display_result["content_summary"] = content_summary
    
    # Include verification details if available
    if "checks" in result:
        checks_summary = {}
        for check_name, check_data in result["checks"].items():
            checks_summary[check_name] = {
                "score": check_data.get("score", 0),
                "confidence": check_data.get("confidence", 0),
                "finding_count": len(check_data.get("findings", [])),
            }
        display_result["checks"] = checks_summary
    
    # Include summary and recommendations if available
    for key in ["summary", "recommendations"]:
        if key in result:
            display_result[key] = result[key]
    
    # Include output files if available
    if "output_files" in result and result["output_files"]:
        display_result["output_files"] = result["output_files"]
    
    # Include extracted data in simplified form if available
    if "extracted_data" in result and result["extracted_data"] is not None:
        extracted_data = result["extracted_data"]
        if isinstance(extracted_data, str):
            # For text extraction, just show a preview
            if len(extracted_data) > 100:
                display_result["extracted_data_preview"] = extracted_data[:100] + "..."
            else:
                display_result["extracted_data_preview"] = extracted_data
        elif isinstance(extracted_data, list):
            # For lists, show count and first few items
            display_result["extracted_data_count"] = len(extracted_data)
            if extracted_data:
                display_result["extracted_data_examples"] = extracted_data[:3]
        elif isinstance(extracted_data, dict):
            # For dictionaries, include key fields
            display_result["extracted_data"] = {
                k: v for k, v in extracted_data.items() 
                if k in ["audio_file", "duration", "image_metadata", "video_metadata", 
                         "content_summary", "language"]
            }
    
    return json.dumps(display_result, indent=2)

def main():
    print("OpenManus Media Analysis Demo")
    print("=" * 60)
    
    # Create Media Analysis Tool
    media_tool = MediaAnalysisTool()
    print("Media Analysis Tool initialized")
    
    # Example media URLs for demonstration
    # In a real application, you'd use actual URLs or local file paths
    example_image_url = "https://example.com/sample_image.jpg"
    example_video_url = "https://example.com/sample_video.mp4"
    example_audio_url = "https://example.com/sample_audio.mp3"
    
    # Section 1: Image Analysis
    print_section("1. Image Analysis")
    
    try:
        # Analyze an image
        print(f"Analyzing image: {example_image_url}")
        image_result = media_tool.analyze_image(example_image_url)
        print(format_result(image_result))
    except Exception as e:
        print(f"Error analyzing image: {e}")
    
    # Section 2: Video Analysis
    print_section("2. Video Analysis")
    
    try:
        # Analyze a video
        print(f"Analyzing video: {example_video_url}")
        video_result = media_tool.analyze_video(example_video_url)
        print(format_result(video_result))
    except Exception as e:
        print(f"Error analyzing video: {e}")
    
    # Section 3: Audio Analysis
    print_section("3. Audio Analysis")
    
    try:
        # Analyze audio
        print(f"Analyzing audio: {example_audio_url}")
        audio_result = media_tool.analyze_audio(example_audio_url)
        print(format_result(audio_result))
    except Exception as e:
        print(f"Error analyzing audio: {e}")
    
    # Section 4: Media Extraction
    print_section("4. Media Extraction")
    
    try:
        # Extract text from an image
        print(f"Extracting text from image: {example_image_url}")
        text_result = media_tool.extract_from_media(example_image_url, "text")
        print(format_result(text_result))
    except Exception as e:
        print(f"Error extracting text: {e}")
    
    # Section 5: Media Verification
    print_section("5. Media Verification")
    
    try:
        # Verify a video
        print(f"Verifying video: {example_video_url}")
        verification_result = media_tool.verify_media(example_video_url)
        print(format_result(verification_result))
    except Exception as e:
        print(f"Error verifying media: {e}")
    
    print("\nMedia Analysis demo complete!")
    print("=" * 60)
    print("Note: This demo uses placeholder implementations. In a real environment,")
    print("the media analysis would use actual AI services like Google Cloud Vision,")
    print("AWS Rekognition, or other specialized media analysis services.")

if __name__ == "__main__":
    main()