#!/usr/bin/env python3
"""
Example script demonstrating the use of the Verification Framework in OpenManus.
This script shows how to verify claims, assess source credibility, and
collect evidence for verification.
"""

import sys
import os
import json
from pprint import pprint

# Add the parent directory to sys.path to import OpenManus modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.tools.verification_framework import VerificationFramework
    from src.tools.media_analysis_tool import MediaAnalysisTool
    from src.tools.api_integration_tool import APIIntegrationTool
except ImportError as e:
    print(f"Error importing Verification Framework: {e}")
    print("Please install the required dependencies.")
    sys.exit(1)

def print_section(title):
    """Helper to print formatted section titles"""
    print(f"\n{title}")
    print("=" * len(title))

def format_result(result, detailed=False):
    """Format verification results for display"""
    if not isinstance(result, dict):
        return str(result)
    
    # Create a simplified version of the result for display
    display_result = {}
    
    # Always include success status and any errors
    display_result["success"] = result.get("success", False)
    if not result.get("success", False) and "error" in result:
        display_result["error"] = result["error"]
        return json.dumps(display_result, indent=2)
    
    # For verification results
    if "verified" in result:
        display_result["verified"] = result["verified"]
        display_result["truth_score"] = result.get("truth_score", 0)
        display_result["confidence"] = result.get("confidence", 0)
        
        if "verification_category" in result:
            display_result["category"] = result["verification_category"]
        
        if "claim" in result:
            display_result["claim"] = result["claim"]
        
        if "sources" in result:
            if result["sources"]:
                display_result["source_count"] = len(result["sources"])
                if detailed:
                    display_result["sources"] = result["sources"]
    
    # For source credibility assessment
    if "credibility_score" in result and "source_url" in result:
        display_result["source_url"] = result["source_url"]
        display_result["credibility_score"] = result["credibility_score"]
        display_result["classification"] = result.get("classification", "unknown")
        
        if detailed and "assessment_factors" in result:
            display_result["factors"] = result["assessment_factors"]
    
    # For evidence collection
    if "collection_id" in result:
        display_result["collection_id"] = result["collection_id"]
        display_result["evidence_count"] = result.get("evidence_count", 0)
        
        if "summary" in result:
            display_result["credibility_score"] = result["summary"].get("overall_credibility", 0)
            display_result["confidence"] = result["summary"].get("confidence", 0)
    
    # For fact/claim/source database operations
    for key in ["fact_id", "source_id", "claim_id", "status"]:
        if key in result:
            display_result[key] = result[key]
    
    return json.dumps(display_result, indent=2)

def main():
    print("OpenManus Verification Framework Demo")
    print("=" * 60)
    
    # Create Verification Framework
    verify = VerificationFramework()
    print("Verification Framework initialized")
    
    # Section 1: Add Facts to Database
    print_section("1. Adding Facts to Database")
    
    # Add some sample facts
    facts = [
        {"fact": "The Earth is approximately 4.54 billion years old.", 
         "source": "https://www.nasa.gov/",
         "category": "science"},
        {"fact": "Water's chemical formula is H2O.", 
         "source": "https://www.acs.org/",
         "category": "science"},
        {"fact": "Paris is the capital of France.", 
         "source": "https://www.britannica.com/",
         "category": "geography"}
    ]
    
    for item in facts:
        result = verify.add_fact(item["fact"], item["source"], item["category"])
        print(f"Added fact: '{item['fact']}'")
        print(format_result(result))
    
    # Section 2: Verify Claims Against Facts
    print_section("2. Verifying Claims Against Facts")
    
    # Verify some claims
    claims = [
        "The Earth is approximately 4.5 billion years old.",
        "Water is made of hydrogen and oxygen.",
        "The Eiffel Tower is located in Rome.",
        "The moon is made of cheese."
    ]
    
    for claim in claims:
        print(f"\nVerifying claim: '{claim}'")
        result = verify.check_fact(claim)
        print(format_result(result))
    
    # Section 3: Source Credibility Assessment
    print_section("3. Source Credibility Assessment")
    
    # Assess credibility of different source types
    sources = [
        "https://www.nasa.gov/",
        "https://example.com/blog/",
        "https://en.wikipedia.org/",
        "https://www.randomsite123456.com/"
    ]
    
    for source in sources:
        print(f"\nAssessing source: {source}")
        result = verify.assess_source_credibility(source)
        print(format_result(result))
    
    # Section 4: Comprehensive Claim Verification
    print_section("4. Comprehensive Claim Verification")
    
    # Verify claims with sources
    complex_claims = [
        {
            "claim": "The average surface temperature on Earth has increased by more than 1°C since pre-industrial times.",
            "sources": ["https://www.ipcc.ch/", "https://www.nasa.gov/", "https://www.noaa.gov/"]
        },
        {
            "claim": "Vaccines contain microchips to track people.",
            "sources": ["https://example.com/conspiracy-blog/"]
        }
    ]
    
    for item in complex_claims:
        print(f"\nVerifying claim: '{item['claim']}'")
        result = verify.verify_claim(item["claim"], item["sources"])
        print(format_result(result, detailed=True))
    
    # Section 5: Evidence Collection
    print_section("5. Evidence Collection")
    
    # Collect evidence for a claim
    claim = "Climate change is causing more frequent and severe weather events."
    sources = [
        "https://www.ipcc.ch/report/ar6/wg2/",
        "https://www.nature.com/articles/s41558-018-0385-5",
        "https://www.noaa.gov/news/climate-reports"
    ]
    media = [
        "https://example.com/graph-temperature-anomalies.png",
        "https://example.com/video-hurricane-documentary.mp4"
    ]
    
    print(f"Collecting evidence for claim: '{claim}'")
    result = verify.collect_evidence(claim, sources, media)
    print(format_result(result))
    
    # Section 6: Framework Statistics
    print_section("6. Verification Framework Statistics")
    
    stats = verify.get_verification_stats()
    print("Framework Statistics:")
    print(json.dumps(stats, indent=2))
    
    print("\nVerification Framework demo complete!")
    print("=" * 60)
    print("Note: This demo uses placeholder implementations. In a real environment,")
    print("the framework would use sophisticated fact-checking methods and external APIs.")

if __name__ == "__main__":
    main()