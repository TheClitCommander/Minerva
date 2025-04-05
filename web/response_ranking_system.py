#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Response Ranking System for Minerva

This module implements a comprehensive system for ranking and storing feedback on model responses,
enabling self-improvement through structured employee evaluations.
"""

import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict, field

# Define ranking criteria
class RankingCriteria:
    ACCURACY = "accuracy"            # Factual correctness
    RELEVANCE = "relevance"          # Relevance to the query
    COMPLETENESS = "completeness"    # Thoroughness of the response
    CLARITY = "clarity"              # Clear and understandable
    CREATIVITY = "creativity"        # Novel or interesting approach
    REASONING = "reasoning"          # Logical reasoning quality
    CODE_QUALITY = "code_quality"    # Quality of code if applicable
    HELPFULNESS = "helpfulness"      # Overall helpfulness to the user
    
    @classmethod
    def get_all_criteria(cls) -> List[str]:
        """Return all available criteria names."""
        return [attr for attr in dir(cls) if not attr.startswith('_') and attr != 'get_all_criteria']
    
    @classmethod
    def get_criteria_description(cls, criterion: str) -> str:
        """Get a description for each criterion."""
        descriptions = {
            cls.ACCURACY: "Factual correctness of the information provided",
            cls.RELEVANCE: "How well the response addresses the specific query",
            cls.COMPLETENESS: "Thoroughness and comprehensiveness of the response",
            cls.CLARITY: "How clear, well-structured, and understandable the response is",
            cls.CREATIVITY: "Originality and innovative thinking in the approach",
            cls.REASONING: "Quality of logical reasoning and analytical thinking",
            cls.CODE_QUALITY: "Quality of code (correctness, efficiency, style, etc.)",
            cls.HELPFULNESS: "Overall value and usefulness to the user",
        }
        return descriptions.get(criterion, "No description available")

@dataclass
class ResponseRanking:
    """Structured representation of a response ranking."""
    
    # Identification
    ranking_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    employee_id: str = None
    
    # Response context
    query: str = None
    response: str = None
    model_name: str = None
    conversation_id: str = None
    
    # Ranking data
    overall_score: int = None  # 1-10 rating
    criteria_scores: Dict[str, int] = field(default_factory=dict)  # Individual criteria scores (1-5)
    feedback_text: str = None  # Optional textual feedback
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResponseRanking':
        """Create a ResponseRanking from a dictionary."""
        return cls(**data)
    
    def get_formatted_timestamp(self) -> str:
        """Get a human-readable timestamp."""
        return datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')

class ResponseRankingSystem:
    """System for recording and analyzing response rankings."""
    
    def __init__(self, storage_path: str = None):
        """Initialize the response ranking system.
        
        Args:
            storage_path: Path to store ranking data. If None, uses default location.
        """
        if storage_path is None:
            # Get directory of this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.storage_path = os.path.join(base_dir, "data", "rankings")
        else:
            self.storage_path = storage_path
            
        # Ensure directory exists
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load existing rankings
        self.rankings: List[ResponseRanking] = []
        self.load_rankings()
    
    def add_ranking(self, 
                   employee_id: str,
                   query: str,
                   response: str,
                   model_name: str,
                   overall_score: int,
                   conversation_id: str = None,
                   criteria_scores: Dict[str, int] = None,
                   feedback_text: str = None,
                   tags: List[str] = None,
                   context: Dict[str, Any] = None) -> str:
        """Add a new response ranking.
        
        Args:
            employee_id: ID of the employee providing the ranking
            query: The original query
            response: The response being ranked
            model_name: Name of the model that generated the response
            overall_score: Overall score (1-10)
            conversation_id: Optional conversation ID for context
            criteria_scores: Optional detailed scores for specific criteria (1-5)
            feedback_text: Optional textual feedback
            tags: Optional tags for categorization
            context: Optional additional context data
            
        Returns:
            The ID of the created ranking
        """
        ranking = ResponseRanking(
            employee_id=employee_id,
            query=query,
            response=response,
            model_name=model_name,
            overall_score=overall_score,
            conversation_id=conversation_id,
            criteria_scores=criteria_scores or {},
            feedback_text=feedback_text,
            tags=tags or [],
            context=context or {}
        )
        
        self.rankings.append(ranking)
        self.save_rankings()
        return ranking.ranking_id
    
    def get_ranking(self, ranking_id: str) -> Optional[ResponseRanking]:
        """Get a ranking by ID."""
        for ranking in self.rankings:
            if ranking.ranking_id == ranking_id:
                return ranking
        return None
    
    def update_ranking(self, ranking_id: str, **kwargs) -> bool:
        """Update a ranking by ID.
        
        Args:
            ranking_id: ID of the ranking to update
            **kwargs: Attributes to update
            
        Returns:
            True if successful, False otherwise
        """
        ranking = self.get_ranking(ranking_id)
        if not ranking:
            return False
            
        # Update ranking
        for key, value in kwargs.items():
            if hasattr(ranking, key):
                setattr(ranking, key, value)
                
        self.save_rankings()
        return True
    
    def delete_ranking(self, ranking_id: str) -> bool:
        """Delete a ranking by ID.
        
        Returns:
            True if successful, False otherwise
        """
        for i, ranking in enumerate(self.rankings):
            if ranking.ranking_id == ranking_id:
                del self.rankings[i]
                self.save_rankings()
                return True
        return False
    
    def get_rankings_by_model(self, model_name: str) -> List[ResponseRanking]:
        """Get all rankings for a specific model."""
        return [r for r in self.rankings if r.model_name == model_name]
    
    def get_rankings_by_employee(self, employee_id: str) -> List[ResponseRanking]:
        """Get all rankings from a specific employee."""
        return [r for r in self.rankings if r.employee_id == employee_id]
    
    def get_rankings_by_score(self, min_score: int = None, max_score: int = None) -> List[ResponseRanking]:
        """Get rankings filtered by overall score."""
        result = self.rankings
        
        if min_score is not None:
            result = [r for r in result if r.overall_score >= min_score]
            
        if max_score is not None:
            result = [r for r in result if r.overall_score <= max_score]
            
        return result
    
    def get_rankings_by_tags(self, tags: List[str], require_all: bool = False) -> List[ResponseRanking]:
        """Get rankings filtered by tags.
        
        Args:
            tags: List of tags to filter by
            require_all: If True, requires all tags to match; if False, any tag matches
            
        Returns:
            List of matching rankings
        """
        if not tags:
            return []
            
        if require_all:
            return [r for r in self.rankings 
                   if all(tag.lower() in [t.lower() for t in r.tags] for tag in tags)]
        else:
            return [r for r in self.rankings 
                   if any(tag.lower() in [t.lower() for t in r.tags] for tag in tags)]
    
    def get_rankings_by_date_range(self, start_time: float = None, end_time: float = None) -> List[ResponseRanking]:
        """Get rankings within a specific date range."""
        result = self.rankings
        
        if start_time is not None:
            result = [r for r in result if r.timestamp >= start_time]
            
        if end_time is not None:
            result = [r for r in result if r.timestamp <= end_time]
            
        return result
    
    def save_rankings(self):
        """Save all rankings to storage."""
        ranking_file = os.path.join(self.storage_path, "response_rankings.json")
        
        # Convert to dictionaries
        ranking_dicts = [r.to_dict() for r in self.rankings]
        
        with open(ranking_file, 'w') as f:
            json.dump(ranking_dicts, f, indent=2)
    
    def load_rankings(self):
        """Load rankings from storage."""
        ranking_file = os.path.join(self.storage_path, "response_rankings.json")
        
        if not os.path.exists(ranking_file):
            self.rankings = []
            return
            
        try:
            with open(ranking_file, 'r') as f:
                ranking_dicts = json.load(f)
                
            self.rankings = [ResponseRanking.from_dict(r) for r in ranking_dicts]
        except Exception as e:
            print(f"Error loading rankings: {e}")
            self.rankings = []
    
    def get_model_performance_stats(self, model_name: str = None) -> Dict[str, Any]:
        """Get performance statistics for a model (or all models).
        
        Args:
            model_name: Optional model name to filter by
            
        Returns:
            Dictionary of performance statistics
        """
        rankings = self.rankings
        if model_name:
            rankings = [r for r in rankings if r.model_name == model_name]
            
        if not rankings:
            return {
                "total_rankings": 0,
                "average_score": 0,
                "criteria_averages": {},
                "score_distribution": {i: 0 for i in range(1, 11)}
            }
        
        # Calculate overall stats
        total = len(rankings)
        overall_scores = [r.overall_score for r in rankings if r.overall_score is not None]
        avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        
        # Calculate score distribution
        score_distribution = {i: 0 for i in range(1, 11)}
        for score in overall_scores:
            if 1 <= score <= 10:
                score_distribution[score] += 1
                
        # Calculate criteria averages
        all_criteria = set()
        for r in rankings:
            all_criteria.update(r.criteria_scores.keys())
            
        criteria_averages = {}
        for criterion in all_criteria:
            scores = [r.criteria_scores.get(criterion) for r in rankings 
                     if criterion in r.criteria_scores and r.criteria_scores[criterion] is not None]
            if scores:
                criteria_averages[criterion] = sum(scores) / len(scores)
        
        return {
            "total_rankings": total,
            "average_score": avg_score,
            "criteria_averages": criteria_averages,
            "score_distribution": score_distribution
        }
    
    def print_model_performance_summary(self, model_name: str = None):
        """Print a readable summary of model performance."""
        if model_name:
            print(f"\n{'='*60}")
            print(f"PERFORMANCE SUMMARY FOR {model_name.upper()}")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print(f"OVERALL MODEL PERFORMANCE SUMMARY")
            print(f"{'='*60}")
            
        stats = self.get_model_performance_stats(model_name)
        
        if stats["total_rankings"] == 0:
            print("No rankings available.")
            return
            
        print(f"Total Rankings: {stats['total_rankings']}")
        print(f"Average Overall Score: {stats['average_score']:.2f}/10")
        
        if stats["criteria_averages"]:
            print("\nAverage Criteria Scores (out of 5):")
            for criterion, score in sorted(stats["criteria_averages"].items(), key=lambda x: x[1], reverse=True):
                desc = RankingCriteria.get_criteria_description(criterion)
                print(f"  {criterion.capitalize()}: {score:.2f} - {desc}")
                
        print("\nScore Distribution:")
        max_count = max(stats["score_distribution"].values())
        for score, count in sorted(stats["score_distribution"].items()):
            bar = "█" * int(20 * count / max_count) if max_count > 0 else ""
            print(f"  {score:2d}: {bar} ({count})")
            
        print(f"{'='*60}\n")
    
    def export_rankings_to_csv(self, output_file: str = None) -> str:
        """Export rankings to a CSV file.
        
        Args:
            output_file: Path to output file. If None, creates a file in the storage directory.
            
        Returns:
            Path to the created CSV file
        """
        import csv
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.storage_path, f"rankings_export_{timestamp}.csv")
            
        # Define CSV columns
        columns = [
            "ranking_id", "timestamp", "employee_id", "model_name", 
            "overall_score", "query", "response", "feedback_text"
        ]
        
        # Add all possible criteria
        all_criteria = set()
        for r in self.rankings:
            all_criteria.update(r.criteria_scores.keys())
        
        criteria_columns = [f"score_{criterion}" for criterion in sorted(all_criteria)]
        columns.extend(criteria_columns)
        
        # Write CSV
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for ranking in self.rankings:
                row = {
                    "ranking_id": ranking.ranking_id,
                    "timestamp": ranking.get_formatted_timestamp(),
                    "employee_id": ranking.employee_id,
                    "model_name": ranking.model_name,
                    "overall_score": ranking.overall_score,
                    "query": ranking.query[:100] + "..." if ranking.query and len(ranking.query) > 100 else ranking.query,
                    "response": ranking.response[:100] + "..." if ranking.response and len(ranking.response) > 100 else ranking.response,
                    "feedback_text": ranking.feedback_text
                }
                
                # Add criteria scores
                for criterion in all_criteria:
                    row[f"score_{criterion}"] = ranking.criteria_scores.get(criterion, "")
                    
                writer.writerow(row)
                
        return output_file


# Example usage
if __name__ == "__main__":
    # Initialize the ranking system
    ranking_system = ResponseRankingSystem()
    
    # Example: Add some rankings
    ranking_system.add_ranking(
        employee_id="emp123",
        query="What's the weather today?",
        response="The weather is sunny with a high of 75°F.",
        model_name="gpt4",
        overall_score=8,
        criteria_scores={
            RankingCriteria.ACCURACY: 4,
            RankingCriteria.RELEVANCE: 5,
            RankingCriteria.CLARITY: 4
        },
        feedback_text="Good response, exactly what I needed.",
        tags=["weather", "quick_response"]
    )
    
    ranking_system.add_ranking(
        employee_id="emp456",
        query="Explain quantum computing",
        response="Quantum computing is a type of computation that harnesses...",
        model_name="claude3",
        overall_score=9,
        criteria_scores={
            RankingCriteria.ACCURACY: 5,
            RankingCriteria.COMPLETENESS: 4,
            RankingCriteria.CLARITY: 5,
            RankingCriteria.REASONING: 5
        },
        feedback_text="Excellent technical explanation.",
        tags=["technical", "educational"]
    )
    
    # Print model performance summary
    ranking_system.print_model_performance_summary()
    
    # Export rankings to CSV
    csv_file = ranking_system.export_rankings_to_csv()
    print(f"Rankings exported to: {csv_file}")
