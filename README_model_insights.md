# Model Insights Dashboard for Minerva

This document provides an overview of the Model Insights Dashboard, a visualization and analytics tool for monitoring the performance of Minerva's AI model selection system.

## Overview

The Model Insights Dashboard provides real-time analytics and visualizations of how different AI models are performing across various query types and complexity levels. It helps administrators and developers understand model performance patterns, identify optimization opportunities, and make data-driven decisions about model selection and configuration.

## Features

### Key Metrics Tracking

- **Total Queries**: Tracks the total number of queries processed by the system
- **Average Quality Score**: Monitors the overall quality of responses across all models
- **Positive Feedback Rate**: Shows the percentage of responses receiving positive user feedback
- **Average Query Complexity**: Tracks the complexity level of user queries

### Visualizations

- **Model Usage by Complexity**: Line chart showing how each model's selection rate varies across different query complexity levels
- **Quality Score by Model**: Bar chart comparing the average quality scores of each model
- **Model Cards**: Detailed cards for each model showing key performance metrics:
  - Selection rate
  - Average quality score
  - Best complexity range
  - Query type specializations

### Recent Activity

- Table of recent model selections showing query details, selected model, complexity score, quality score, and user feedback

## Architecture

The Model Insights Dashboard consists of:

1. **Frontend**: HTML/CSS/JavaScript dashboard with Chart.js for visualization
2. **Backend**: Python-based analytics system integrated with Minerva's existing infrastructure
3. **Data Collection**: Integration points within the message processing and feedback system

### Key Components

#### Model Insights Manager (`model_insights_manager.py`)

This module manages the collection, analysis, and retrieval of model performance data:

- Records model selections and associated metadata
- Tracks user feedback on model responses
- Calculates performance metrics across different dimensions
- Provides formatted data for dashboard visualization

#### Dashboard Template (`model_insights.html`)

A responsive, interactive dashboard built with:
- Bootstrap for layout and components
- Chart.js for data visualization
- Custom CSS for styling

#### App Integration

The dashboard is integrated with Minerva's web application through:
- A new route in `app.py` for accessing the dashboard
- Integration points in message processing logic to record model selection events
- Enhanced feedback recording to track user satisfaction with different models

## Data Collection

The system collects the following data points:

- **Query Information**: Text, complexity score, query type tags
- **Model Selection**: Which model was chosen and which models were considered
- **Response Quality**: Objective quality scores and subjective user feedback
- **Temporal Data**: Timestamps to enable trend analysis over time

## Usage

To access the Model Insights Dashboard:

1. Navigate to the `/insights` endpoint in your Minerva installation
2. Use the time period selectors (Day/Week/Month) to view different time ranges
3. Click on different visualizations to explore specific aspects of model performance
4. Use the "Refresh Data" button to get the latest performance metrics

## Implementation Details

### Query Complexity Assessment

The system uses a combination of factors to estimate query complexity:
- Length and structure of the query
- Presence of technical terms or specialized vocabulary
- Number of distinct questions or requirements
- Need for external knowledge or context

### Query Tagging

Queries are automatically tagged based on content analysis:
- Code-related queries
- Explanations
- Comparisons
- Short queries

### Model Performance Evaluation

Models are evaluated based on multiple criteria:
- Quality scores from objective metrics
- User feedback (positive/negative)
- Performance across different complexity levels
- Specialization in certain query types

## Future Enhancements

Planned improvements to the Model Insights Dashboard include:

1. **Advanced Analytics**: Deeper statistical analysis of model performance patterns
2. **User-Specific Insights**: Analysis of model performance for individual users
3. **Recommendation Engine**: AI-driven suggestions for optimizing model selection rules
4. **Real-Time Monitoring**: Live updating of dashboard metrics as new queries are processed
5. **Export Capabilities**: Options to export performance data for external analysis

## Conclusion

The Model Insights Dashboard provides a powerful tool for understanding and optimizing Minerva's AI model selection system. By visualizing performance data across different dimensions, it enables data-driven decisions about model configuration and helps identify patterns that can lead to improved user experiences.
