"""
Verification Framework for OpenManus.

This module provides a comprehensive framework for verifying claims and information,
including fact checking, source credibility assessment, evidence collection,
and confidence metrics.
"""

import os
import json
import logging
import tempfile
import hashlib
import datetime
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path

from src.tools.api_integration_tool import APIIntegrationTool
from src.tools.media_analysis_tool import MediaAnalysisTool

# Set up logging
logger = logging.getLogger(__name__)

class VerificationError(Exception):
    """Base exception for verification errors."""
    pass

class VerificationFramework:
    """
    Framework for verifying claims and information.
    
    This tool provides functionality for fact checking, source assessment,
    evidence collection, and confidence scoring for information verification.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the verification framework.
        
        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        
        # Set up the base paths
        self.base_path = Path(self.config.get("base_path", "data/verification"))
        self.db_path = Path(self.config.get("db_path", "data/verification/db"))
        self.evidence_path = Path(self.config.get("evidence_path", "data/verification/evidence"))
        
        # Create directories if they don't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.evidence_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different types of evidence
        for subdir in ["facts", "sources", "claims", "media"]:
            (self.evidence_path / subdir).mkdir(parents=True, exist_ok=True)
        
        # Initialize dependent tools
        self.api_tool = APIIntegrationTool(self.config.get("api_integration", {}))
        self.media_tool = MediaAnalysisTool(self.config.get("media_analysis", {}))
        
        # Initialize fact database
        self.fact_db_path = self.db_path / "facts.json"
        self.facts = self._load_facts()
        
        # Initialize source credibility database
        self.sources_db_path = self.db_path / "sources.json"
        self.sources = self._load_sources()
        
        # Initialize claims database
        self.claims_db_path = self.db_path / "claims.json"
        self.claims = self._load_claims()
        
        # Statistics tracking
        self.stats = {
            "verifications_performed": 0,
            "facts_checked": 0,
            "sources_assessed": 0,
            "claims_validated": 0,
            "evidence_collected": 0
        }
    
    def _load_facts(self) -> Dict[str, Any]:
        """Load facts database from file or initialize a new one."""
        if self.fact_db_path.exists():
            try:
                with open(self.fact_db_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading facts database: {e}")
                # Return default structure if file is corrupted
        
        # Default structure for facts database
        return {
            "metadata": {
                "created": datetime.datetime.now().isoformat(),
                "updated": datetime.datetime.now().isoformat(),
                "version": "1.0.0",
                "count": 0
            },
            "facts": {}
        }
    
    def _save_facts(self) -> bool:
        """Save facts database to file."""
        try:
            self.facts["metadata"]["updated"] = datetime.datetime.now().isoformat()
            self.facts["metadata"]["count"] = len(self.facts["facts"])
            
            with open(self.fact_db_path, 'w') as f:
                json.dump(self.facts, f, indent=2)
            return True
        except (IOError, TypeError) as e:
            logger.error(f"Error saving facts database: {e}")
            return False
    
    def _load_sources(self) -> Dict[str, Any]:
        """Load sources database from file or initialize a new one."""
        if self.sources_db_path.exists():
            try:
                with open(self.sources_db_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading sources database: {e}")
                # Return default structure if file is corrupted
        
        # Default structure for sources database
        return {
            "metadata": {
                "created": datetime.datetime.now().isoformat(),
                "updated": datetime.datetime.now().isoformat(),
                "version": "1.0.0",
                "count": 0
            },
            "sources": {}
        }
    
    def _save_sources(self) -> bool:
        """Save sources database to file."""
        try:
            self.sources["metadata"]["updated"] = datetime.datetime.now().isoformat()
            self.sources["metadata"]["count"] = len(self.sources["sources"])
            
            with open(self.sources_db_path, 'w') as f:
                json.dump(self.sources, f, indent=2)
            return True
        except (IOError, TypeError) as e:
            logger.error(f"Error saving sources database: {e}")
            return False
    
    def _load_claims(self) -> Dict[str, Any]:
        """Load claims database from file or initialize a new one."""
        if self.claims_db_path.exists():
            try:
                with open(self.claims_db_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading claims database: {e}")
                # Return default structure if file is corrupted
        
        # Default structure for claims database
        return {
            "metadata": {
                "created": datetime.datetime.now().isoformat(),
                "updated": datetime.datetime.now().isoformat(),
                "version": "1.0.0",
                "count": 0
            },
            "claims": {}
        }
    
    def _save_claims(self) -> bool:
        """Save claims database to file."""
        try:
            self.claims["metadata"]["updated"] = datetime.datetime.now().isoformat()
            self.claims["metadata"]["count"] = len(self.claims["claims"])
            
            with open(self.claims_db_path, 'w') as f:
                json.dump(self.claims, f, indent=2)
            return True
        except (IOError, TypeError) as e:
            logger.error(f"Error saving claims database: {e}")
            return False
    
    def _generate_id(self, text: str) -> str:
        """Generate a unique ID for a fact, source, or claim."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def add_fact(self, fact: str, source_url: str, category: str = "general", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a verified fact to the database.
        
        Args:
            fact: The factual statement.
            source_url: URL to the source of the fact.
            category: Category for the fact (e.g., "science", "history", "politics").
            metadata: Additional metadata for the fact.
            
        Returns:
            Dictionary with information about the added fact.
        """
        metadata = metadata or {}
        fact_id = self._generate_id(fact)
        
        # Check if fact already exists
        if fact_id in self.facts["facts"]:
            logger.info(f"Fact already exists: {fact_id}")
            return {
                "success": True,
                "fact_id": fact_id,
                "status": "exists",
                "fact": self.facts["facts"][fact_id]
            }
        
        # Add the new fact
        timestamp = datetime.datetime.now().isoformat()
        self.facts["facts"][fact_id] = {
            "id": fact_id,
            "fact": fact,
            "source_url": source_url,
            "category": category,
            "created": timestamp,
            "last_verified": timestamp,
            "metadata": metadata
        }
        
        # Save the updated database
        success = self._save_facts()
        
        # Update stats
        self.stats["facts_checked"] += 1
        
        return {
            "success": success,
            "fact_id": fact_id,
            "status": "added" if success else "error",
            "fact": self.facts["facts"].get(fact_id)
        }
    
    def check_fact(self, statement: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check if a statement is factual against the verification database.
        
        Args:
            statement: The statement to verify.
            options: Additional options for the verification.
                - threshold: Similarity threshold for matching facts (default: 0.8)
                - max_results: Maximum number of matching facts to return (default: 5)
                - verify_if_missing: Attempt to verify with external sources if not in database (default: True)
            
        Returns:
            Dictionary with verification results including truth score and confidence.
        """
        options = options or {}
        threshold = options.get("threshold", 0.8)
        max_results = options.get("max_results", 5)
        verify_if_missing = options.get("verify_if_missing", True)
        
        # In a real implementation, this would use sophisticated similarity algorithms
        # or call an external API for fact-checking
        # For now, we're using a simple mock implementation
        
        # Update stats
        self.stats["verifications_performed"] += 1
        self.stats["facts_checked"] += 1
        
        # Generate a hash for direct lookup
        statement_id = self._generate_id(statement)
        
        # Check for exact matches
        if statement_id in self.facts["facts"]:
            return {
                "success": True,
                "verified": True,
                "truth_score": 1.0,
                "confidence": 1.0,
                "statement": statement,
                "matches": [self.facts["facts"][statement_id]],
                "method": "exact_match"
            }
        
        # Simulate fuzzy matching
        # In a real implementation, this would use semantic similarity or other NLP techniques
        
        # Mock implementation - assume we found some similar facts
        matches = []
        truth_score = 0.0
        confidence = 0.0
        
        # Simulate finding matching facts from database based on similarity
        # In reality, this would use vector embeddings or other similarity methods
        if len(self.facts["facts"]) > 0:
            # Simulate finding some similar facts
            sample_facts = list(self.facts["facts"].values())[:min(5, len(self.facts["facts"]))]
            
            for fact in sample_facts:
                # Simulate calculating similarity
                similarity = 0.5  # Mock similarity value
                
                if similarity >= threshold:
                    matches.append({
                        "fact": fact,
                        "similarity": similarity
                    })
                    
                    # Limit matches to max_results
                    if len(matches) >= max_results:
                        break
            
            # Calculate truth score and confidence based on matches
            if matches:
                # Average similarity of top matches
                avg_similarity = sum(match["similarity"] for match in matches) / len(matches)
                truth_score = avg_similarity
                confidence = min(0.8, avg_similarity)  # Cap confidence at 0.8 for fuzzy matches
        
        # If no matches found in database and verify_if_missing is True,
        # attempt to verify with external sources
        if not matches and verify_if_missing:
            # Simulate external verification
            # In a real implementation, this would call external fact-checking APIs
            external_verification = {
                "verified": False,
                "truth_score": 0.3,  # Mock value
                "confidence": 0.4,  # Mock value
                "source": "simulated_external_check"
            }
            
            # Use external verification results
            truth_score = external_verification["truth_score"]
            confidence = external_verification["confidence"]
            
            # Add to our database if it's verified with high confidence
            if external_verification["verified"] and confidence > 0.8:
                self.add_fact(
                    statement,
                    "https://example.com/external_verification",  # Placeholder
                    "verified_external"
                )
        
        return {
            "success": True,
            "verified": truth_score > 0.7,  # Consider verified if above 0.7
            "truth_score": truth_score,
            "confidence": confidence,
            "statement": statement,
            "matches": [match["fact"] for match in matches],
            "method": "fuzzy_match" if matches else "external_verification" if verify_if_missing else "no_match"
        }
    
    def add_source(self, source_url: str, name: str = "", category: str = "general", 
                   credibility_score: float = 0.5, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a source to the credibility database.
        
        Args:
            source_url: URL of the source.
            name: Name of the source (e.g., publication name).
            category: Category for the source (e.g., "news", "academic", "social_media").
            credibility_score: Initial credibility score (0.0 to 1.0).
            metadata: Additional metadata for the source.
            
        Returns:
            Dictionary with information about the added source.
        """
        metadata = metadata or {}
        source_id = self._generate_id(source_url)
        
        # Normalize URL
        source_url = source_url.lower().strip()
        
        # Extract domain if no name provided
        if not name:
            # Simple domain extraction - would be more sophisticated in real implementation
            if source_url.startswith(("http://", "https://")):
                # Remove protocol
                domain = source_url.split("//")[1]
                # Remove path and get domain
                domain = domain.split("/")[0]
                name = domain
        
        # Check if source already exists
        if source_id in self.sources["sources"]:
            logger.info(f"Source already exists: {source_id}")
            # Update last_updated timestamp
            self.sources["sources"][source_id]["last_updated"] = datetime.datetime.now().isoformat()
            self._save_sources()
            
            return {
                "success": True,
                "source_id": source_id,
                "status": "exists",
                "source": self.sources["sources"][source_id]
            }
        
        # Add the new source
        timestamp = datetime.datetime.now().isoformat()
        self.sources["sources"][source_id] = {
            "id": source_id,
            "url": source_url,
            "name": name,
            "category": category,
            "credibility_score": max(0.0, min(1.0, credibility_score)),  # Ensure between 0 and 1
            "created": timestamp,
            "last_updated": timestamp,
            "fact_count": 0,
            "metadata": metadata
        }
        
        # Save the updated database
        success = self._save_sources()
        
        # Update stats
        self.stats["sources_assessed"] += 1
        
        return {
            "success": success,
            "source_id": source_id,
            "status": "added" if success else "error",
            "source": self.sources["sources"].get(source_id)
        }
    
    def assess_source_credibility(self, source_url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Assess the credibility of a source.
        
        Args:
            source_url: URL of the source to assess.
            options: Additional options for assessment.
                - update_db: Whether to update the sources database (default: True)
                - check_external: Whether to check external credibility databases (default: True)
                - detailed: Whether to return detailed assessment (default: False)
            
        Returns:
            Dictionary with credibility assessment results.
        """
        options = options or {}
        update_db = options.get("update_db", True)
        check_external = options.get("check_external", True)
        detailed = options.get("detailed", False)
        
        # Normalize URL
        source_url = source_url.lower().strip()
        source_id = self._generate_id(source_url)
        
        # Update stats
        self.stats["verifications_performed"] += 1
        self.stats["sources_assessed"] += 1
        
        # Check if source exists in database
        source_in_db = source_id in self.sources["sources"]
        source_data = self.sources["sources"].get(source_id, {})
        
        # Factors to consider for credibility scoring
        factors = {
            "domain_credibility": 0.0,
            "content_quality": 0.0,
            "transparency": 0.0,
            "historical_accuracy": 0.0,
            "fact_citation": 0.0,
            "author_expertise": 0.0,
            "bias_assessment": 0.0
        }
        
        # If in database, start with existing score
        if source_in_db:
            credibility_score = source_data.get("credibility_score", 0.5)
            
            # Simulate analysis of various credibility factors
            for factor in factors:
                # In a real implementation, this would be a sophisticated analysis
                factors[factor] = max(0.0, min(1.0, credibility_score + (0.2 * (0.5 - hash(factor + source_url) % 100 / 100.0))))
        else:
            # Simulate assessing a new source
            
            # In a real implementation, this would:
            # 1. Analyze the domain reputation
            # 2. Check for transparency indicators
            # 3. Assess content quality
            # 4. Check citation practices
            # 5. Evaluate bias and political leaning
            
            # For now, simulate some reasonable values
            base_score = 0.5
            
            # Basic domain reputation check
            if "example.com" in source_url:
                factors["domain_credibility"] = 0.7
            elif ".gov" in source_url or ".edu" in source_url:
                factors["domain_credibility"] = 0.9
            elif ".org" in source_url:
                factors["domain_credibility"] = 0.75
            else:
                factors["domain_credibility"] = 0.5
                
            # Simulate other factors
            for factor in factors:
                if factor != "domain_credibility":
                    # Generate a reasonable value based on domain credibility
                    factors[factor] = max(0.0, min(1.0, factors["domain_credibility"] + (0.2 * (0.5 - hash(factor + source_url) % 100 / 100.0))))
            
            # Check external credibility databases if requested
            if check_external:
                # In a real implementation, this would call external APIs
                # For now, simulate external check results
                external_scores = {
                    "external_source_1": 0.65,
                    "external_source_2": 0.7
                }
                
                # Average external scores
                external_avg = sum(external_scores.values()) / len(external_scores) if external_scores else 0.5
                
                # Weight external scores in overall assessment
                factors["external_assessment"] = external_avg
            
            # Calculate overall credibility score
            credibility_score = sum(factors.values()) / len(factors)
            
            # Add to database if requested
            if update_db:
                # Extract domain for name
                domain = source_url.split("//")[-1].split("/")[0] if "//" in source_url else source_url.split("/")[0]
                
                self.add_source(
                    source_url,
                    name=domain,
                    category="unknown",
                    credibility_score=credibility_score,
                    metadata={"assessment_factors": factors}
                )
        
        # Confidence in assessment
        confidence = 0.9 if source_in_db else (0.7 if check_external else 0.5)
        
        # Credibility classification
        classification = "high_credibility" if credibility_score >= 0.8 else \
                         "medium_credibility" if credibility_score >= 0.6 else \
                         "low_credibility" if credibility_score >= 0.4 else \
                         "very_low_credibility"
        
        result = {
            "success": True,
            "source_url": source_url,
            "credibility_score": credibility_score,
            "confidence": confidence,
            "classification": classification,
            "in_database": source_in_db
        }
        
        # Add detailed assessment if requested
        if detailed:
            result["assessment_factors"] = factors
            result["source_data"] = source_data if source_in_db else None
        
        return result
    
    def add_claim(self, claim: str, truth_score: float, sources: List[str], 
                 category: str = "general", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a verified claim to the database.
        
        Args:
            claim: The claim statement.
            truth_score: Truth score (0.0 to 1.0) for the claim.
            sources: List of source URLs supporting the verification.
            category: Category for the claim (e.g., "politics", "science").
            metadata: Additional metadata for the claim.
            
        Returns:
            Dictionary with information about the added claim.
        """
        metadata = metadata or {}
        claim_id = self._generate_id(claim)
        
        # Check if claim already exists
        if claim_id in self.claims["claims"]:
            logger.info(f"Claim already exists: {claim_id}")
            # Update with new verification
            self.claims["claims"][claim_id]["verification_history"].append({
                "timestamp": datetime.datetime.now().isoformat(),
                "truth_score": truth_score,
                "sources": sources
            })
            # Update last_verified timestamp and current score
            self.claims["claims"][claim_id]["last_verified"] = datetime.datetime.now().isoformat()
            self.claims["claims"][claim_id]["truth_score"] = truth_score
            self.claims["claims"][claim_id]["sources"] = sources
            self._save_claims()
            
            return {
                "success": True,
                "claim_id": claim_id,
                "status": "updated",
                "claim": self.claims["claims"][claim_id]
            }
        
        # Add the new claim
        timestamp = datetime.datetime.now().isoformat()
        self.claims["claims"][claim_id] = {
            "id": claim_id,
            "claim": claim,
            "truth_score": max(0.0, min(1.0, truth_score)),  # Ensure between 0 and 1
            "sources": sources,
            "category": category,
            "created": timestamp,
            "last_verified": timestamp,
            "verification_history": [{
                "timestamp": timestamp,
                "truth_score": truth_score,
                "sources": sources
            }],
            "metadata": metadata
        }
        
        # Save the updated database
        success = self._save_claims()
        
        # Update stats
        self.stats["claims_validated"] += 1
        
        return {
            "success": success,
            "claim_id": claim_id,
            "status": "added" if success else "error",
            "claim": self.claims["claims"].get(claim_id)
        }
    
    def verify_claim(self, claim: str, sources: Optional[List[str]] = None, 
                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Verify a claim using the verification framework.
        
        Args:
            claim: The claim to verify.
            sources: Optional list of source URLs for the claim.
            options: Additional options for verification.
                - threshold: Truth score threshold for verification (default: 0.7)
                - check_sources: Whether to assess source credibility (default: True)
                - store_result: Whether to store verification result (default: True)
                - category: Claim category (default: "general")
            
        Returns:
            Dictionary with verification results including truth score and confidence.
        """
        sources = sources or []
        options = options or {}
        threshold = options.get("threshold", 0.7)
        check_sources = options.get("check_sources", True)
        store_result = options.get("store_result", True)
        category = options.get("category", "general")
        
        # Update stats
        self.stats["verifications_performed"] += 1
        self.stats["claims_validated"] += 1
        
        # Check if claim already exists in database
        claim_id = self._generate_id(claim)
        claim_in_db = claim_id in self.claims["claims"]
        claim_data = self.claims["claims"].get(claim_id, {})
        
        # If claim exists and was recently verified, return stored results
        if claim_in_db:
            last_verified = datetime.datetime.fromisoformat(claim_data.get("last_verified", "2000-01-01T00:00:00"))
            now = datetime.datetime.now()
            if (now - last_verified).days < 7:  # If verified within last week
                return {
                    "success": True,
                    "verified": claim_data.get("truth_score", 0.0) >= threshold,
                    "truth_score": claim_data.get("truth_score", 0.0),
                    "confidence": 0.9,  # High confidence for recent DB entry
                    "claim": claim,
                    "sources": claim_data.get("sources", []),
                    "method": "database",
                    "claim_id": claim_id
                }
        
        # First, check the factual basis of the claim
        fact_check = self.check_fact(claim)
        
        # Source credibility assessments, if enabled
        source_assessments = []
        if check_sources and sources:
            for source_url in sources:
                assessment = self.assess_source_credibility(source_url)
                source_assessments.append(assessment)
            
            # Average source credibility scores
            avg_source_credibility = sum(assess["credibility_score"] for assess in source_assessments) / len(source_assessments)
        else:
            avg_source_credibility = 0.5  # Default if no sources provided
        
        # Collect and analyze evidence
        evidence = {
            "factual_basis": fact_check.get("truth_score", 0.0),
            "source_credibility": avg_source_credibility,
            "consistency": 0.8,  # Placeholder for claim consistency check
            "counter_evidence": 0.1  # Placeholder for counter-evidence
        }
        
        # Calculate weighted truth score
        # In a real implementation, this would use a more sophisticated model
        weights = {
            "factual_basis": 0.5,
            "source_credibility": 0.3,
            "consistency": 0.1,
            "counter_evidence": 0.1
        }
        
        truth_score = sum(evidence[k] * weights[k] for k in evidence)
        
        # Calculate confidence
        # Lower confidence if sources aren't credible or fact check confidence is low
        fact_confidence = fact_check.get("confidence", 0.5)
        source_confidence = 0.8 if avg_source_credibility > 0.7 else 0.5
        
        confidence = 0.7 * fact_confidence + 0.3 * source_confidence
        
        # Store the verification result if requested
        if store_result:
            self.add_claim(
                claim=claim,
                truth_score=truth_score,
                sources=sources,
                category=category,
                metadata={
                    "evidence": evidence,
                    "source_assessments": [
                        {"url": assess["source_url"], "score": assess["credibility_score"]}
                        for assess in source_assessments
                    ],
                    "confidence": confidence
                }
            )
        
        # Determine verification status
        verified = truth_score >= threshold
        
        # Determine verification method
        method = "comprehensive" if (check_sources and sources) else "fact_check_only"
        
        return {
            "success": True,
            "verified": verified,
            "truth_score": truth_score,
            "confidence": confidence,
            "claim": claim,
            "sources": sources,
            "method": method,
            "claim_id": claim_id,
            "evidence_summary": evidence,
            "source_credibility": avg_source_credibility if sources else None,
            "verification_category": "true" if truth_score >= 0.8 else
                                     "mostly_true" if truth_score >= 0.6 else
                                     "mixed" if truth_score >= 0.4 else
                                     "mostly_false" if truth_score >= 0.2 else
                                     "false"
        }
    
    def collect_evidence(self, claim: str, sources: List[str], media_urls: Optional[List[str]] = None,
                        options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collect and analyze evidence for a claim.
        
        Args:
            claim: The claim to collect evidence for.
            sources: List of source URLs to analyze for evidence.
            media_urls: Optional list of media URLs related to the claim (images, videos).
            options: Additional options for evidence collection.
                - analyze_media: Whether to analyze media content (default: True)
                - check_sources: Whether to assess source credibility (default: True)
                - max_sources: Maximum number of sources to analyze (default: 5)
            
        Returns:
            Dictionary with collected evidence and analysis.
        """
        media_urls = media_urls or []
        options = options or {}
        analyze_media = options.get("analyze_media", True)
        check_sources = options.get("check_sources", True)
        max_sources = options.get("max_sources", 5)
        
        # Update stats
        self.stats["verifications_performed"] += 1
        self.stats["evidence_collected"] += 1
        
        # Generate a unique ID for this evidence collection
        collection_id = f"evidence_{self._generate_id(claim)}_{int(datetime.datetime.now().timestamp())}"
        
        # Initialize evidence collection
        evidence_collection = {
            "id": collection_id,
            "claim": claim,
            "timestamp": datetime.datetime.now().isoformat(),
            "sources": sources[:max_sources],  # Limit to max_sources
            "media": media_urls,
            "evidence_items": [],
            "summary": {}
        }
        
        # Create directory for storing this evidence
        evidence_dir = self.evidence_path / "claims" / collection_id
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Check sources
        source_evidence = []
        if check_sources:
            for source_url in sources[:max_sources]:
                try:
                    # Assess source credibility
                    assessment = self.assess_source_credibility(source_url, {"detailed": True})
                    
                    # Extract content from source (simulated)
                    # In a real implementation, this would fetch and analyze the content
                    content_relevance = 0.7  # Placeholder for content relevance to claim
                    
                    # Add to source evidence
                    source_evidence.append({
                        "url": source_url,
                        "credibility": assessment.get("credibility_score", 0.5),
                        "classification": assessment.get("classification", "unknown"),
                        "relevance": content_relevance
                    })
                except Exception as e:
                    logger.error(f"Error collecting evidence from source {source_url}: {e}")
                    # Add error entry
                    source_evidence.append({
                        "url": source_url,
                        "error": str(e),
                        "status": "failed"
                    })
        
        # Add source evidence to collection
        evidence_collection["evidence_items"].append({
            "type": "source_analysis",
            "items": source_evidence,
            "count": len(source_evidence),
            "average_credibility": sum(item.get("credibility", 0) for item in source_evidence) / len(source_evidence) if source_evidence else 0
        })
        
        # Analyze media if requested
        media_evidence = []
        if analyze_media and media_urls:
            for media_url in media_urls:
                try:
                    # Determine media type
                    if media_url.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                        # Analyze image
                        analysis = self.media_tool.analyze_image(media_url)
                    elif media_url.lower().endswith((".mp4", ".avi", ".mov", ".wmv", ".webm")):
                        # Analyze video
                        analysis = self.media_tool.analyze_video(media_url)
                    elif media_url.lower().endswith((".mp3", ".wav", ".ogg", ".m4a")):
                        # Analyze audio
                        analysis = self.media_tool.analyze_audio(media_url)
                    else:
                        # Default to video for unknown types (like most social media URLs)
                        analysis = self.media_tool.analyze_video(media_url)
                    
                    # Verify media authenticity
                    verification = self.media_tool.verify_media(media_url)
                    
                    # Add to media evidence
                    if analysis.get("success", False):
                        media_evidence.append({
                            "url": media_url,
                            "type": analysis.get("analysis_type", "unknown"),
                            "verification_score": verification.get("verification_score", 0.0),
                            "confidence": verification.get("confidence", 0.0),
                            "relevance_to_claim": 0.8  # Placeholder for relevance assessment
                        })
                except Exception as e:
                    logger.error(f"Error analyzing media {media_url}: {e}")
                    # Add error entry
                    media_evidence.append({
                        "url": media_url,
                        "error": str(e),
                        "status": "failed"
                    })
        
        # Add media evidence to collection
        if media_evidence:
            evidence_collection["evidence_items"].append({
                "type": "media_analysis",
                "items": media_evidence,
                "count": len(media_evidence),
                "average_verification": sum(item.get("verification_score", 0) for item in media_evidence) / len(media_evidence) if media_evidence else 0
            })
        
        # Check fact database for supporting or contradicting facts
        fact_check = self.check_fact(claim)
        
        # Add fact check to evidence
        evidence_collection["evidence_items"].append({
            "type": "fact_check",
            "truth_score": fact_check.get("truth_score", 0.0),
            "confidence": fact_check.get("confidence", 0.0),
            "matches": fact_check.get("matches", [])
        })
        
        # Generate evidence summary
        evidence_summary = {
            "overall_credibility": 0.0,
            "source_credibility": 0.0,
            "media_authenticity": 0.0,
            "factual_basis": 0.0,
            "consistency": 0.0,
            "confidence": 0.0
        }
        
        # Calculate summary metrics
        for item in evidence_collection["evidence_items"]:
            if item["type"] == "source_analysis":
                evidence_summary["source_credibility"] = item.get("average_credibility", 0.0)
            elif item["type"] == "media_analysis":
                evidence_summary["media_authenticity"] = item.get("average_verification", 0.0)
            elif item["type"] == "fact_check":
                evidence_summary["factual_basis"] = item.get("truth_score", 0.0)
        
        # Calculate overall credibility score
        # In a real implementation, this would use a more sophisticated model
        if evidence_summary["source_credibility"] > 0 and evidence_summary["factual_basis"] > 0:
            evidence_summary["overall_credibility"] = (
                0.5 * evidence_summary["factual_basis"] +
                0.3 * evidence_summary["source_credibility"] +
                0.2 * evidence_summary["media_authenticity"]
            )
            evidence_summary["confidence"] = 0.7
        elif evidence_summary["factual_basis"] > 0:
            evidence_summary["overall_credibility"] = evidence_summary["factual_basis"]
            evidence_summary["confidence"] = 0.5
        else:
            evidence_summary["overall_credibility"] = 0.0
            evidence_summary["confidence"] = 0.0
        
        # Save evidence collection to file
        evidence_file = evidence_dir / "evidence.json"
        try:
            with open(evidence_file, 'w') as f:
                json.dump(evidence_collection, f, indent=2)
        except (IOError, TypeError) as e:
            logger.error(f"Error saving evidence collection: {e}")
        
        # Add summary to collection
        evidence_collection["summary"] = evidence_summary
        
        return {
            "success": True,
            "collection_id": collection_id,
            "claim": claim,
            "evidence_count": sum(item.get("count", 1) for item in evidence_collection["evidence_items"]),
            "credibility_score": evidence_summary["overall_credibility"],
            "confidence": evidence_summary["confidence"],
            "summary": evidence_summary,
            "evidence_path": str(evidence_file)
        }
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the verification framework.
        
        Returns:
            Dictionary with verification statistics.
        """
        return {
            "success": True,
            "stats": self.stats,
            "database_stats": {
                "facts": len(self.facts["facts"]),
                "sources": len(self.sources["sources"]),
                "claims": len(self.claims["claims"]),
                "last_updated": {
                    "facts": self.facts["metadata"]["updated"],
                    "sources": self.sources["metadata"]["updated"],
                    "claims": self.claims["metadata"]["updated"]
                }
            }
        }