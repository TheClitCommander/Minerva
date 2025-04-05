#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Response Feedback Handler

Handles the collection, storage, and analysis of user feedback on chat responses.
This is a simpler user-focused feedback system that tracks whether responses were helpful.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class FeedbackHandler:
    """Handles user feedback on AI responses."""
    
    def __init__(self, storage_path: str = None):
        """Initialize the feedback handler.
        
        Args:
            storage_path: Path to store feedback data. If None, uses default location.
        """
        if storage_path is None:
            # Get directory of this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.storage_path = os.path.join(base_dir, "data", "feedback")
        else:
            self.storage_path = storage_path
            
        # Ensure directory exists
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load existing feedback
        self.feedback_data = self.load_feedback()
    
    def submit_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record user feedback on a response.
        
        Args:
            feedback_data: Dictionary containing feedback information
                Required keys:
                - message_id: ID of the message
                - feedback: 'helpful' or 'not_helpful'
                Optional keys:
                - reason: User's explanation for the feedback
                - query: The original user query
                - response: The AI's response
                - model: Model that generated the response
                - timestamp: When the feedback was submitted
                
        Returns:
            Dictionary with success status and feedback ID
        """
        if not feedback_data.get('message_id'):
            raise ValueError("message_id is required")
            
        if feedback_data.get('feedback') not in ['helpful', 'not_helpful']:
            raise ValueError("feedback must be 'helpful' or 'not_helpful'")
        
        # Add timestamp if not provided
        if 'timestamp' not in feedback_data:
            feedback_data['timestamp'] = datetime.now().isoformat()
            
        # Add feedback ID
        feedback_id = f"fb_{int(time.time())}_{hash(feedback_data['message_id']) % 10000:04d}"
        feedback_data['feedback_id'] = feedback_id
        
        # Store feedback
        self.feedback_data.append(feedback_data)
        self.save_feedback()
        
        logger.info(f"Recorded feedback {feedback_id}: {feedback_data['feedback']} - {feedback_data.get('reason', '')[:50]}")
        
        return {
            'success': True,
            'feedback_id': feedback_id
        }
    
    def load_feedback(self) -> List[Dict[str, Any]]:
        """Load feedback data from storage."""
        feedback_file = os.path.join(self.storage_path, "user_feedback.json")
        
        if not os.path.exists(feedback_file):
            return []
            
        try:
            with open(feedback_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading feedback data: {e}")
            return []
    
    def save_feedback(self):
        """Save feedback data to storage."""
        feedback_file = os.path.join(self.storage_path, "user_feedback.json")
        
        try:
            with open(feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving feedback data: {e}")
    
    def get_feedback_stats(self, model: str = None) -> Dict[str, Any]:
        """Get feedback statistics, optionally filtered by model.
        
        Args:
            model: Optional model name to filter by
            
        Returns:
            Dictionary of feedback statistics
        """
        feedback = self.feedback_data
        if model:
            feedback = [f for f in feedback if f.get('model') == model]
            
        if not feedback:
            return {
                'total_feedback': 0,
                'helpful_count': 0,
                'not_helpful_count': 0,
                'helpful_percentage': 0
            }
        
        total = len(feedback)
        helpful = sum(1 for f in feedback if f.get('feedback') == 'helpful')
        not_helpful = total - helpful
        
        # Get most common reasons for not helpful feedback
        not_helpful_reasons = []
        for f in feedback:
            if f.get('feedback') == 'not_helpful' and f.get('reason'):
                not_helpful_reasons.append(f.get('reason'))
        
        # Count reason occurrences (simple implementation)
        reason_counts = {}
        for reason in not_helpful_reasons:
            # Use first 50 chars as key to group similar reasons
            key = reason[:50].lower().strip()
            reason_counts[key] = reason_counts.get(key, 0) + 1
        
        # Sort by frequency
        common_reasons = sorted(
            [(count, reason) for reason, count in reason_counts.items()],
            reverse=True
        )[:5]  # Top 5 reasons
        
        return {
            'total_feedback': total,
            'helpful_count': helpful,
            'not_helpful_count': not_helpful,
            'helpful_percentage': (helpful / total) * 100 if total > 0 else 0,
            'common_not_helpful_reasons': [
                {'count': count, 'reason': reason} 
                for count, reason in common_reasons
            ]
        }
    
    def get_model_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance statistics for all models.
        
        Returns:
            Dictionary mapping model names to their statistics
        """
        # Get all models that have feedback
        models = set()
        for feedback in self.feedback_data:
            if feedback.get('model'):
                models.add(feedback.get('model'))
        
        # Get stats for each model
        model_stats = {}
        for model in models:
            model_stats[model] = self.get_feedback_stats(model)
            
        return model_stats
    
    def get_feedback_by_message(self, message_id: str) -> List[Dict[str, Any]]:
        """Get all feedback for a specific message."""
        return [f for f in self.feedback_data if f.get('message_id') == message_id]
    
    def get_feedback_by_date_range(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Get feedback within a specific date range."""
        result = self.feedback_data
        
        if start_date:
            result = [f for f in result if f.get('timestamp', '') >= start_date]
            
        if end_date:
            result = [f for f in result if f.get('timestamp', '') <= end_date]
            
        return result
        
    def get_admin_stats(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive statistics for admin dashboard.
        
        Args:
            start_date: Optional start date for filtering feedback
            end_date: Optional end date for filtering feedback
            
        Returns:
            Dict with detailed feedback statistics
        """
        # Filter feedback by date range if provided
        filtered_data = self.feedback_data
        
        if start_date or end_date:
            filtered_data = []
            for item in self.feedback_data:
                # Parse the timestamp
                try:
                    timestamp = item.get('timestamp')
                    if timestamp:
                        item_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        
                        # Check if the item is within the date range
                        if start_date and item_date < start_date:
                            continue
                        if end_date and item_date > end_date:
                            continue
                    
                    filtered_data.append(item)
                except (ValueError, TypeError):
                    # If timestamp parsing fails, include the item
                    filtered_data.append(item)
        
        # Calculate overall statistics
        total_feedback = len(filtered_data)
        helpful_count = sum(1 for item in filtered_data if item.get('feedback') == 'helpful')
        not_helpful_count = total_feedback - helpful_count
        
        helpful_percentage = (helpful_count / total_feedback * 100) if total_feedback > 0 else 0
        
        # Calculate model statistics
        model_stats = {}
        for item in filtered_data:
            model = item.get('model', 'unknown')
            
            if model not in model_stats:
                model_stats[model] = {
                    'helpful': 0,
                    'not_helpful': 0
                }
                
            if item.get('feedback') == 'helpful':
                model_stats[model]['helpful'] += 1
            else:
                model_stats[model]['not_helpful'] += 1
        
        # Calculate time-based statistics (group by day)
        time_stats = {}
        for item in filtered_data:
            timestamp = item.get('timestamp')
            if not timestamp:
                continue
                
            try:
                item_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                day_key = item_date.strftime('%Y-%m-%d')
                
                if day_key not in time_stats:
                    time_stats[day_key] = {
                        'helpful': 0,
                        'not_helpful': 0
                    }
                    
                if item.get('feedback') == 'helpful':
                    time_stats[day_key]['helpful'] += 1
                else:
                    time_stats[day_key]['not_helpful'] += 1
            except (ValueError, TypeError):
                continue
        
        # Analyze by query type
        query_type_stats = self._analyze_query_types(filtered_data)
        
        # Get common feedback reasons (enhanced format)
        feedback_reasons = self._analyze_feedback_reasons(filtered_data)
        
        # Get model recommendations based on feedback
        model_adjustments = {}
        if total_feedback >= 20:  # Only show recommendations with enough data
            try:
                # Import here to avoid circular imports
                from feedback_analyzer import FeedbackAnalyzer
                analyzer = FeedbackAnalyzer()
                
                # Get model recommendations (use existing data to avoid duplicate analysis)
                model_stats_list = [{'model': model, 'stats': stats} for model, stats in model_stats.items()]
                model_adjustments = analyzer._get_model_adjustment_recommendations(
                    model_stats_list,
                    query_type_stats
                )
            except Exception as e:
                logging.error(f"Error getting model recommendations: {e}")
        
        # Compile all statistics
        return {
            'overall': {
                'helpful': helpful_count,
                'not_helpful': not_helpful_count,
                'total': total_feedback,
                'helpful_percentage': helpful_percentage
            },
            'by_model': model_stats,
            'by_time': time_stats,
            'by_query_type': query_type_stats,
            'common_reasons': {}, # Legacy format for backward compatibility
            'feedback_reasons': feedback_reasons,
            'model_adjustments': model_adjustments
        }
        
    def _analyze_query_types(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Analyze feedback by query type.
        
        This categorizes queries into different types and counts feedback for each type.
        Uses enhanced categorization that aligns with the feedback analyzer.
        
        Args:
            feedback_data: List of feedback items to analyze
            
        Returns:
            Dict with query type statistics
        """
        # Define detection patterns for different query types (expanded and aligned with analyzer)
        query_types = {
            'technical_coding': ['code', 'programming', 'function', 'method', 'class', 'python', 'javascript', 
                              'java', 'api', 'framework', 'library', 'bug', 'syntax', 'error', 'implement',
                              'script', 'module', 'algorithm'],
            'technical_math': ['calculate', 'equation', 'formula', 'solve', 'math', 'computation', 'numerical',
                             'statistics', 'probability', 'algebra', 'calculus', 'arithmetic'],
            'creative': ['create', 'generate', 'imagine', 'design', 'story', 'idea', 'creative', 'content',
                       'write', 'essay', 'poem', 'fiction', 'art', 'invent'],
            'how_to': ['how to', 'steps to', 'guide for', 'tutorial', 'instructions', 'procedure for',
                     'walkthrough', 'way to'],
            'definition': ['what is', 'what are', 'define', 'meaning of', 'definition', 'describe',
                         'explain what', 'concept of'],
            'explanation': ['why', 'explain why', 'reason for', 'cause of', 'explain the reason',
                          'explain how', 'clarify why'],
            'factual': ['when', 'where', 'who', 'which', 'what year', 'in what', 'history of',
                      'facts about', 'information on', 'details about'],
            'comparison': ['compare', 'versus', 'vs', 'difference between', 'similarities between',
                         'better than', 'pros and cons', 'advantages and disadvantages'],
            'list_steps': ['list', 'steps', 'process', 'procedure', 'guide', 'sequence',
                         'outline', 'summarize', 'bullet points'],
            'reasoning': ['analyze', 'evaluate', 'consider', 'argument', 'implications',
                        'assess', 'critique', 'review', 'examine', 'investigate'],
            'general': []
        }
        
        # Try to use session identified query type first if available
        query_type_from_session = {}
        for item in feedback_data:
            if 'query_type' in item and 'session_id' in item:
                session_id = item.get('session_id')
                query_type = item.get('query_type')
                
                # Only count if it's a valid query type
                if query_type in query_types or query_type == 'general':
                    query_type_from_session[session_id] = query_type
                    
        # Initialize counters for all query types
        results = {}
        for query_type in query_types:
            results[query_type] = {
                'helpful': 0,
                'not_helpful': 0,
                'top_models': {}
            }
        
        # Categorize each query
        for item in feedback_data:
            query = item.get('query', '').lower()
            session_id = item.get('session_id')
            model = item.get('model', 'unknown')
            
            if not query and not session_id:
                continue
                
            # Try to get the query type from session first
            if session_id and session_id in query_type_from_session:
                detected_type = query_type_from_session[session_id]
            else:
                # Determine query type from text
                detected_type = 'general'
                
                for query_type, keywords in query_types.items():
                    if query_type == 'general':
                        continue
                        
                    if any(keyword in query for keyword in keywords):
                        detected_type = query_type
                        break
            
            # Count feedback for this query type
            if item.get('feedback') == 'helpful':
                results[detected_type]['helpful'] += 1
            else:
                results[detected_type]['not_helpful'] += 1
                
            # Track model performance by query type
            if model != 'unknown':
                if model not in results[detected_type]['top_models']:
                    results[detected_type]['top_models'][model] = {
                        'helpful': 0,
                        'not_helpful': 0
                    }
                
                if item.get('feedback') == 'helpful':
                    results[detected_type]['top_models'][model]['helpful'] += 1
                else:
                    results[detected_type]['top_models'][model]['not_helpful'] += 1
        
        return results
        
    def _analyze_feedback_reasons(self, feedback_data: List[Dict[str, Any]], limit: int = 10) -> Dict[str, Dict[str, Any]]:
        """Analyze and extract common feedback reasons with enhanced categorization.
        
        Args:
            feedback_data: List of feedback items to analyze
            limit: Maximum number of reasons to return
            
        Returns:
            Dict with detailed reason statistics and categorization
        """
        # Extract reasons and categorize by feedback type
        helpful_reasons = []
        not_helpful_reasons = []
        
        for item in feedback_data:
            reason = item.get('reason', '').strip()
            if not reason:
                continue
                
            if item.get('feedback') == 'helpful':
                helpful_reasons.append(reason)
            else:
                not_helpful_reasons.append(reason)
        
        # Count frequency of reasons by category
        helpful_counts = self._count_reasons(helpful_reasons)
        not_helpful_counts = self._count_reasons(not_helpful_reasons)
        
        # Get top reasons by category
        top_helpful = dict(sorted(helpful_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:limit])
        top_not_helpful = dict(sorted(not_helpful_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:limit])
        
        # Categorize not helpful reasons
        categories = {
            "incorrect": ["incorrect", "wrong", "inaccurate", "error", "mistake", "false"],
            "irrelevant": ["irrelevant", "not related", "off topic", "unrelated", "didn't answer"],
            "confusing": ["confusing", "unclear", "vague", "hard to understand", "ambiguous"],
            "incomplete": ["incomplete", "partial", "not enough", "missing", "didn't finish", "cut off"],
            "tone": ["tone", "condescending", "rude", "patronizing", "abrupt"],
            "tech_issue": ["tech", "error", "bug", "didn't work", "crash", "failed"]
        }
        
        # Categorize the reasons
        categorized = {}
        for category, keywords in categories.items():
            categorized[category] = 0
            
            for reason, data in not_helpful_counts.items():
                if any(keyword in reason for keyword in keywords):
                    categorized[category] += data['count']
        
        # Return comprehensive analysis
        return {
            "helpful": top_helpful,
            "not_helpful": top_not_helpful,
            "categories": categorized,
            "total_helpful_reasons": len(helpful_reasons),
            "total_not_helpful_reasons": len(not_helpful_reasons)
        }
        
    def _count_reasons(self, reasons: List[str]) -> Dict[str, Dict[str, Any]]:
        """Count and group similar reasons.
        
        Args:
            reasons: List of feedback reasons
            
        Returns:
            Dictionary mapping grouped reasons to counts and examples
        """
        reason_data = {}
        
        for reason in reasons:
            # Simplify reason for better grouping
            simplified = self._simplify_reason(reason)
            
            if simplified in reason_data:
                reason_data[simplified]['count'] += 1
                # Keep track of original reasons (max 3 examples per group)
                if len(reason_data[simplified]['examples']) < 3:
                    reason_data[simplified]['examples'].append(reason)
            else:
                reason_data[simplified] = {
                    'count': 1,
                    'examples': [reason]
                }
        
        return reason_data
    
    def _simplify_reason(self, reason: str) -> str:
        """Simplify a feedback reason for better grouping.
        
        This function normalizes reasons by removing stopwords, punctuation,
        and focusing on key terms to group similar feedback.
        Uses basic NLP techniques for better grouping.
        
        Args:
            reason: Original feedback reason
            
        Returns:
            Simplified version of the reason
        """
        # Start with lowercase
        simple = reason.lower()
        
        # Remove punctuation except apostrophes
        simple = ''.join(c for c in simple if c.isalnum() or c.isspace() or c == "'")
        
        # English stopwords to remove for better matching
        stopwords = {
            'a', 'an', 'the', 'and', 'but', 'or', 'because', 'as', 'if', 'when', 'than', 'that', 'which',
            'this', 'these', 'those', 'it', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'having', 'do', 'does', 'did', 'doing', 'to', 'at', 'by', 'for', 'with', 'about', 'against',
            'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'from', 'up', 'down',
            'in', 'out', 'on', 'off', 'over', 'under', 'again', 'then', 'once', 'here', 'there', 'all', 'any',
            'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now'
        }
        
        # Filter out stopwords
        words = [w for w in simple.split() if w not in stopwords]
        if words:
            simple = ' '.join(words)
        
        # Normalize common variations of the same concept
        replacements = {
            'incorrect': ['wrong', 'not correct', 'not right', 'error', 'mistake'],
            'irrelevant': ['not relevant', 'unrelated', 'off topic', 'not related', 'doesnt relate'],
            'inaccurate': ['not accurate', 'not factual', 'false information'],
            'incomplete': ['not complete', 'missing', 'partial', 'not enough', 'needs more'],
            'confusing': ['unclear', 'hard understand', 'doesnt make sense', 'ambiguous', 'vague']
        }
        
        for target, variations in replacements.items():
            if any(variation in simple for variation in variations):
                # Replace all variations with the normalized term
                for variation in variations:
                    if variation in simple:
                        simple = simple.replace(variation, target)
        
        # Extract key phrases (2-3 word combinations) if present
        key_phrases = []
        words = simple.split()
        if len(words) >= 2:
            for i in range(len(words) - 1):
                key_phrases.append(words[i] + ' ' + words[i+1])
        
        # If we found key phrases, use the most significant one
        if key_phrases:
            # Find the phrase most likely to be meaningful (simple heuristic)
            key_phrase = max(key_phrases, key=len)
            # If the key phrase captures enough meaning, use it
            if len(key_phrase) >= 7:  # Arbitrary threshold
                return key_phrase
        
        # Truncate to a reasonable length
        if len(simple) > 100:
            simple = simple[:100]
            
        return simple
    
    def export_feedback_to_csv(self, output_file: str = None) -> str:
        """Export feedback data to a CSV file.
        
        Args:
            output_file: Path to output file. If None, creates a file in the storage directory.
            
        Returns:
            Path to the created CSV file
        """
        import csv
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.storage_path, f"feedback_export_{timestamp}.csv")
            
        # Define CSV columns
        columns = [
            "feedback_id", "message_id", "timestamp", "feedback", "reason", 
            "model", "query", "response"
        ]
        
        # Write CSV
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for feedback in self.feedback_data:
                row = {col: feedback.get(col, '') for col in columns}
                
                # Truncate long fields
                if row['query'] and len(row['query']) > 100:
                    row['query'] = row['query'][:97] + '...'
                    
                if row['response'] and len(row['response']) > 100:
                    row['response'] = row['response'][:97] + '...'
                    
                writer.writerow(row)
                
        return output_file
    
    def print_feedback_summary(self):
        """Print a summary of the feedback data."""
        stats = self.get_feedback_stats()
        model_stats = self.get_model_performance()
        
        print("\n" + "=" * 60)
        print("FEEDBACK SUMMARY")
        print("=" * 60)
        print(f"Total Feedback: {stats['total_feedback']}")
        
        if stats['total_feedback'] > 0:
            print(f"Helpful: {stats['helpful_count']} ({stats['helpful_percentage']:.1f}%)")
            print(f"Not Helpful: {stats['not_helpful_count']} ({100 - stats['helpful_percentage']:.1f}%)")
            
            if stats['common_not_helpful_reasons']:
                print("\nCommon Reasons for 'Not Helpful' Feedback:")
                for reason_data in stats['common_not_helpful_reasons']:
                    print(f"  • ({reason_data['count']}) {reason_data['reason']}...")
            
            print("\nModel Performance:")
            for model, model_data in model_stats.items():
                if model_data['total_feedback'] > 0:
                    print(f"  {model}: {model_data['helpful_percentage']:.1f}% helpful ({model_data['total_feedback']} responses)")
        
        print("=" * 60)


# Example usage
if __name__ == "__main__":
    # Initialize the feedback handler
    feedback_handler = FeedbackHandler()
    
    # Example: Add some feedback
    feedback_handler.submit_feedback({
        'message_id': 'msg123',
        'feedback': 'helpful',
        'reason': 'The response was clear and answered my question completely.',
        'query': 'How do I reset my password?',
        'response': 'To reset your password, go to the login page and click on "Forgot Password"...',
        'model': 'gpt4'
    })
    
    feedback_handler.submit_feedback({
        'message_id': 'msg456',
        'feedback': 'not_helpful',
        'reason': 'The response didn\'t address my specific question about Python.',
        'query': 'How do I use list comprehensions in Python?',
        'response': 'Python is a programming language...',
        'model': 'mistral7b'
    })
    
    # Print feedback summary
    feedback_handler.print_feedback_summary()
