from flask import Flask, render_template, send_from_directory, jsonify, request
import os
import random
import json
import uuid

app = Flask(__name__)

# Sample enhanced model info for testing
def generate_sample_model_info():
    # Create enhanced model info structure based on the memory
    models = ['gpt-4', 'claude-3', 'gemini-pro', 'mistral-large']
    
    # Generate ranking scores that sum to 1
    base_scores = [random.uniform(0.7, 0.95) for _ in range(len(models))]
    total = sum(base_scores)
    normalized_scores = [score/total for score in base_scores]
    
    # Create ranked_responses with detailed info
    ranked_responses = []
    for i, model in enumerate(models):
        ranked_responses.append({
            "model": model,
            "score": normalized_scores[i],
            "reasoning": f"Performed well on {random.choice(['relevance', 'correctness', 'coherence', 'creativity'])}",
            "capabilities": {
                "technical": random.uniform(0.7, 0.95),
                "creativity": random.uniform(0.7, 0.95),
                "reasoning": random.uniform(0.7, 0.95)
            }
        })
    
    # Sort by score descending
    ranked_responses.sort(key=lambda x: x["score"], reverse=True)
    
    # Create model weights for blending
    model_weights = {}
    for i, model in enumerate(models):
        model_weights[model] = normalized_scores[i] * 100
    
    return {
        "task_type": random.choice(["technical", "creative", "factual", "reasoning"]),
        "complexity": random.randint(3, 9),
        "tags": random.sample(["code", "math", "history", "science", "explanation"], 2),
        "models_used": models,
        "best_model": ranked_responses[0]["model"],
        "response_source": "blended",
        "blended": True,
        "ranked_responses": ranked_responses,
        "blending_info": {
            "quality": random.uniform(0.85, 0.98),
            "strategy": random.choice(["technical_blend", "comparative_blend", "general_blend"]),
            "model_weights": model_weights
        },
        "query_analysis": {
            "type": random.choice(["technical", "creative", "factual", "reasoning"]),
            "confidence": random.uniform(0.85, 0.98)
        }
    }

@app.route('/')
def index():
    return send_from_directory('.', 'simplest_test.html')

@app.route('/api/v1/advanced-think-tank', methods=['POST'])
def advanced_think_tank():
    data = request.json
    message = data.get('message', '')
    
    # Create a realistic response with enhanced model info
    response = {
        "response": f"I understand your question about '{message}'. The Think Tank has analyzed this and here's the response...\n\nBased on the available information, this appears to be a {random.choice(['technical', 'conceptual', 'theoretical'])} question. Here are some key points to consider:\n\n1. First important point\n2. Second relevant consideration\n3. Additional context that might be helpful\n\nIn conclusion, this is a simulated Think Tank response for testing purposes.",
        "model_info": generate_sample_model_info()
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
