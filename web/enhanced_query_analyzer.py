#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Query Analyzer for Minerva's Think Tank Mode

This module provides sophisticated query analysis capabilities including:
- Advanced query classification with subcategories
- More nuanced complexity scoring
- Feature extraction for query routing
- Context-aware tagging
"""

import logging
import re
import string
from typing import Dict, List, Any, Tuple, Set, Optional
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define query categories and subcategories
QUERY_CATEGORIES = {
    "technical": {
        "subcategories": [
            "programming",       # Code, debugging, implementation
            "data_science",      # ML, statistics, data analysis
            "system_design",     # Architecture, design patterns
            "devops",            # Deployment, CI/CD, containers
            "troubleshooting",   # Errors, debugging
        ],
        "indicators": {
            "programming": ["code", "function", "algorithm", "programming", "library", 
                            "syntax", "variable", "class", "object", "method", "api"],
            "data_science": ["machine learning", "neural network", "statistics", 
                             "data analysis", "regression", "classification", "model training"],
            "system_design": ["architecture", "design pattern", "microservice", 
                              "database schema", "api design", "system design", "structure"],
            "devops": ["docker", "kubernetes", "ci/cd", "deployment", "jenkins", 
                       "github action", "gitlab", "aws", "cloud", "infrastructure"],
            "troubleshooting": ["error", "debug", "fix", "issue", "problem", "not working", 
                                "exception", "crash", "failure", "bug"]
        }
    },
    "creative": {
        "subcategories": [
            "writing",           # Stories, essays, articles
            "artistic",          # Visual arts, music, design
            "brainstorming",     # Ideas, concepts, innovation
        ],
        "indicators": {
            "writing": ["write", "story", "poem", "narrative", "creative", "fiction", 
                       "character", "plot", "screenplay", "essay", "article"],
            "artistic": ["design", "visual", "image", "music", "song", "artistic", 
                         "aesthetic", "style", "color scheme", "composition"],
            "brainstorming": ["idea", "brainstorm", "concept", "innovative", "creative solution", 
                             "generate ideas", "possibilities", "alternatives", "options"]
        }
    },
    "analytical": {
        "subcategories": [
            "comparison",        # Compare/contrast
            "evaluation",        # Pros/cons, critique
            "explanation",       # How/why questions
            "trend_analysis",    # Trends, forecasting
        ],
        "indicators": {
            "comparison": ["compare", "contrast", "versus", "differences", "similarities", 
                          "pros and cons", "advantages and disadvantages"],
            "evaluation": ["evaluate", "assess", "critique", "review", "analyze", 
                          "strengths and weaknesses", "effectiveness"],
            "explanation": ["explain", "how does", "why does", "reason for", "mechanism", 
                           "process", "cause and effect", "underlying", "principles"],
            "trend_analysis": ["trend", "forecast", "predict", "future", "evolution", 
                              "development", "trajectory", "pattern", "historical"]
        }
    },
    "factual": {
        "subcategories": [
            "definition",        # What is X
            "knowledge",         # General knowledge questions
            "procedural",        # How to do X
            "historical",        # Historical facts
        ],
        "indicators": {
            "definition": ["what is", "define", "meaning of", "definition", "concept of", 
                          "explain the term", "refers to"],
            "knowledge": ["who", "what", "where", "when", "which", "fact", "information", 
                         "true or false", "correct", "accurate"],
            "procedural": ["how to", "steps to", "process for", "method of", "procedure", 
                          "instructions", "guide", "tutorial"],
            "historical": ["history", "historical", "in the past", "origin", "evolution", 
                          "development", "timeline", "ancient", "traditional"]
        }
    }
}

# Technical domain vocabulary for more accurate detection
DOMAIN_VOCABULARY = {
    "programming_languages": ["python", "javascript", "java", "c++", "typescript", "ruby", "go", "rust", 
                             "php", "swift", "kotlin", "scala", "perl", "r", "bash", "powershell", "dart"],
    "frameworks": ["react", "vue", "angular", "django", "flask", "express", "spring", "rails", 
                  "laravel", "tensorflow", "pytorch", "keras", "flask", "fastapi", "next.js", "symfony"],
    "databases": ["sql", "mysql", "postgresql", "mongodb", "sqlite", "dynamodb", "firestore", 
                 "redis", "cassandra", "neo4j", "elasticsearch", "mariadb", "oracle", "snowflake"],
    "cloud_services": ["aws", "azure", "gcp", "google cloud", "lambda", "ec2", "s3", "cloudfront", 
                      "firebase", "heroku", "digitalocean", "kubernetes", "docker"]
}

class EnhancedQueryAnalyzer:
    """Implements enhanced query analysis with sophisticated classification and scoring"""
    
    def __init__(self):
        """Initialize the query analyzer"""
        logger.info("Enhanced Query Analyzer initialized")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on a user query.
        
        Args:
            query: The user's query/message
            
        Returns:
            Dictionary containing various analysis results
        """
        # Clean and normalize the query
        normalized_query = self._normalize_query(query)
        
        # Extract key features
        query_length = len(query.split())
        question_count = query.count('?')
        has_code_block = bool(re.search(r'```.*```', query, re.DOTALL))
        
        # Perform analysis
        tags = self.extract_tags(query)
        query_category, subcategory = self.classify_query(query)
        complexity = self.calculate_complexity(query)
        technical_domains = self.detect_technical_domains(query)
        
        # Compile results
        return {
            "query_category": query_category,
            "subcategory": subcategory,
            "complexity": complexity,
            "tags": list(tags),
            "technical_domains": technical_domains,
            "features": {
                "length": query_length,
                "questions": question_count,
                "has_code": has_code_block,
                "is_technical": query_category == "technical",
                "is_creative": query_category == "creative",
                "is_analytical": query_category == "analytical"
            }
        }
    
    def classify_query(self, query: str) -> Tuple[str, str]:
        """
        Determine the most likely category and subcategory for a query.
        
        Args:
            query: The user query
            
        Returns:
            Tuple of (category, subcategory)
        """
        query_lower = query.lower()
        
        # Count matches for each category and subcategory
        category_scores = {}
        subcategory_scores = {}
        
        for category, data in QUERY_CATEGORIES.items():
            category_score = 0
            
            # Check each subcategory
            for subcategory, indicators in data["indicators"].items():
                subcategory_score = 0
                
                # Count indicator matches
                for indicator in indicators:
                    if indicator in query_lower:
                        matches = len(re.findall(r'\b' + re.escape(indicator) + r'\b', query_lower))
                        subcategory_score += matches
                
                subcategory_scores[subcategory] = subcategory_score
                category_score += subcategory_score
            
            category_scores[category] = category_score
        
        # Determine the best category and subcategory
        best_category = max(category_scores.items(), key=lambda x: x[1])
        
        # If no clear indicators were found, use heuristics for factual queries
        if best_category[1] == 0:
            # Factual questions often start with who, what, where, when, how
            factual_starters = ["who", "what", "where", "when", "how", "which", "why"]
            words = query_lower.split()
            if words and words[0] in factual_starters:
                best_category = ("factual", 1)
        
        # Find the best subcategory within the selected category
        if best_category[1] > 0:
            category = best_category[0]
            relevant_subcategories = {sub: subcategory_scores[sub] 
                                     for sub in QUERY_CATEGORIES[category]["subcategories"]}
            
            best_subcategory = max(relevant_subcategories.items(), key=lambda x: x[1])
            
            if best_subcategory[1] > 0:
                return category, best_subcategory[0]
            else:
                return category, QUERY_CATEGORIES[category]["subcategories"][0]
        
        # Default to factual if nothing else matches
        return "factual", "knowledge"
    
    def calculate_complexity(self, query: str) -> int:
        """
        Calculate the complexity of a query on a scale of 1-10.
        Uses multiple factors including length, structure, vocabulary, and topic.
        
        Args:
            query: The user's query
            
        Returns:
            Complexity score (1-10)
        """
        # Base complexity starts at 2
        complexity = 2
        
        # Normalize and tokenize
        query_lower = query.lower()
        words = query_lower.split()
        
        # 1. Length factor - longer queries tend to be more complex
        if len(words) > 100:
            complexity += 3
        elif len(words) > 50:
            complexity += 2
        elif len(words) > 20:
            complexity += 1
        
        # 2. Technical vocabulary factor
        technical_terms = [
            "algorithm", "function", "variable", "framework", "implementation", 
            "parameter", "optimization", "complexity", "architecture", "paradigm",
            "recursion", "encryption", "asynchronous", "concurrent", "polymorphism",
            "inheritance", "middleware", "microservice", "authentication", "database"
        ]
        
        tech_count = sum(1 for term in technical_terms if term in query_lower)
        complexity += min(2, tech_count // 2 + (1 if tech_count % 2 else 0))
        
        # 3. Structure complexity
        # Multiple questions indicate more complex requests
        question_count = query.count("?")
        if question_count > 3:
            complexity += 2
        elif question_count > 1:
            complexity += 1
        
        # Multi-part or conditional requests
        if any(connector in query_lower for connector in 
               ["and then", "after that", "if...then", "depending on", "alternatively"]):
            complexity += 1
        
        # 4. Code blocks are typically more complex
        if re.search(r'```.*```', query, re.DOTALL):
            complexity += 2
        
        # 5. Abstract concepts
        abstract_concepts = [
            "philosophy", "theory", "concept", "principle", "framework", 
            "methodology", "paradigm", "perspective", "abstract", "theoretical"
        ]
        
        if any(concept in query_lower for concept in abstract_concepts):
            complexity += 1
        
        # Cap at range 1-10
        return max(1, min(10, complexity))
    
    def extract_tags(self, query: str) -> Set[str]:
        """
        Extract relevant tags from the query.
        
        Args:
            query: The user's query
            
        Returns:
            Set of tags
        """
        query_lower = query.lower()
        tags = set()
        
        # Technical tags
        if re.search(r'\bcode\b|\bprogram\b|\bfunction\b|\balgorithm\b|\bdebug\b', query_lower):
            tags.add("code")
        
        # Language-specific tags
        for lang in DOMAIN_VOCABULARY["programming_languages"]:
            if re.search(r'\b' + re.escape(lang) + r'\b', query_lower):
                tags.add("specific_language")
                tags.add(f"lang_{lang}")
                break
        
        # Creative tags
        if re.search(r'\bwrite\b|\bstory\b|\bpoem\b|\bcreative\b|\bartistic\b', query_lower):
            tags.add("creative")
        
        # Mathematical/scientific
        if re.search(r'\bequation\b|\bcalcul\w+\b|\bphysics\b|\bchemistry\b|\bmath\b', query_lower):
            tags.add("scientific")
        
        # Data-related
        if re.search(r'\bdata\b|\bdatabase\b|\bsql\b|\banalysis\b|\bstatistics\b', query_lower):
            tags.add("data")
        
        # Educational/learning
        if re.search(r'\bexplain\b|\bteach\b|\blearn\b|\bunderstand\b|\bconcept\b', query_lower):
            tags.add("educational")
        
        # Needs reasoning
        if re.search(r'\bconsider\b|\bevaluate\b|\banalyze\b|\bcompare\b|\bthink\b', query_lower):
            tags.add("reasoning")
        
        return tags
    
    def detect_technical_domains(self, query: str) -> Dict[str, float]:
        """
        Detect technical domains relevant to the query and assign confidence scores.
        
        Args:
            query: The user's query
            
        Returns:
            Dictionary mapping domains to confidence scores (0.0-1.0)
        """
        query_lower = query.lower()
        domains = {}
        
        # Check for domain-specific vocabulary
        for domain, terms in DOMAIN_VOCABULARY.items():
            matches = 0
            for term in terms:
                if re.search(r'\b' + re.escape(term) + r'\b', query_lower):
                    matches += 1
            
            if matches > 0:
                # Calculate confidence score based on proportion of matched terms
                confidence = min(1.0, matches / max(5, len(terms) / 3))
                domains[domain] = round(confidence, 2)
        
        return domains
    
    def _normalize_query(self, query: str) -> str:
        """
        Clean and normalize a query for analysis.
        
        Args:
            query: The original query
            
        Returns:
            Normalized query
        """
        # Convert to lowercase
        normalized = query.lower()
        
        # Remove code blocks for text analysis
        normalized = re.sub(r'```.*?```', ' CODE_BLOCK ', normalized, flags=re.DOTALL)
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()


# Create a singleton instance for easy importing
query_analyzer = EnhancedQueryAnalyzer()


# Test function to demonstrate the analyzer
def test_query_analyzer():
    """Test the query analyzer with sample queries."""
    test_queries = [
        "Write a Python function to find the longest substring without repeating characters",
        "What's the difference between REST and GraphQL?",
        "Write a short story about a robot who discovers emotions",
        "Can you help me debug this JavaScript code? ```function broken() { const x = [1,2,3; return x; }```",
        "Explain the theory of relativity in simple terms",
        "What are the best practices for securing a Node.js application?",
        "Analyze the impact of artificial intelligence on healthcare in the next decade",
        "What is the capital of France?",
        "How do I cook pasta al dente?",
        "Design a database schema for a hospital management system"
    ]
    
    for query in test_queries:
        print(f"\n{'=' * 80}")
        print(f"QUERY: {query}")
        results = query_analyzer.analyze_query(query)
        
        print(f"CATEGORY: {results['query_category']} / {results['subcategory']}")
        print(f"COMPLEXITY: {results['complexity']}/10")
        print(f"TAGS: {', '.join(results['tags'])}")
        
        if results['technical_domains']:
            print("TECHNICAL DOMAINS:")
            for domain, confidence in results['technical_domains'].items():
                print(f"  - {domain}: {confidence:.2f}")
        
        print(f"FEATURES:")
        for feature, value in results['features'].items():
            print(f"  - {feature}: {value}")


if __name__ == "__main__":
    test_query_analyzer()
