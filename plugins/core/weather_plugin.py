"""
Minerva AI - Weather Plugin

This plugin provides weather information capabilities to Minerva.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional

# Import the base Plugin class
from plugins.base import Plugin

logger = logging.getLogger("minerva.plugins.weather")


class WeatherPlugin(Plugin):
    """Plugin for retrieving weather information."""
    
    plugin_id = "weather"
    plugin_name = "Weather Information"
    plugin_version = "1.0.0"
    plugin_description = "Provides weather information capabilities to Minerva"
    plugin_author = "Minerva Team"
    plugin_tags = ["weather", "information", "utility"]
    
    def __init__(self):
        """Initialize the weather plugin."""
        super().__init__()
        self.api_key = None
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.config_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "config",
            "weather_plugin.json"
        )
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        # Load config
        if not self._load_config():
            logger.warning("Weather plugin config not found or invalid")
            # Still initialize, but functionality will be limited
        
        self._is_initialized = True
        logger.info("Weather plugin initialized")
        return True
    
    def _load_config(self) -> bool:
        """
        Load the plugin configuration.
        
        Returns:
            bool: True if config was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key")
                return self.api_key is not None
            return False
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading weather plugin config: {e}")
            return False
    
    def _save_config(self) -> bool:
        """
        Save the plugin configuration.
        
        Returns:
            bool: True if config was saved successfully, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump({"api_key": self.api_key}, f, indent=2)
            return True
        except IOError as e:
            logger.error(f"Error saving weather plugin config: {e}")
            return False
    
    def set_api_key(self, api_key: str) -> bool:
        """
        Set the API key for the weather service.
        
        Args:
            api_key: API key for OpenWeatherMap
            
        Returns:
            bool: True if the API key was set successfully, False otherwise
        """
        self.api_key = api_key
        return self._save_config()
    
    def get_current_weather(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Get the current weather for a location.
        
        Args:
            location: Location to get weather for (city name or coordinates)
            
        Returns:
            Dictionary with weather information or None if retrieval failed
        """
        if not self.api_key:
            logger.error("API key not set for weather plugin")
            return {
                "error": "API key not configured",
                "message": "Please set the OpenWeatherMap API key in the plugin settings"
            }
        
        try:
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            # Extract relevant information
            result = {
                "location": data.get("name"),
                "country": data.get("sys", {}).get("country"),
                "temperature": data.get("main", {}).get("temp"),
                "feels_like": data.get("main", {}).get("feels_like"),
                "humidity": data.get("main", {}).get("humidity"),
                "pressure": data.get("main", {}).get("pressure"),
                "weather": data.get("weather", [{}])[0].get("main"),
                "description": data.get("weather", [{}])[0].get("description"),
                "wind_speed": data.get("wind", {}).get("speed"),
                "wind_direction": data.get("wind", {}).get("deg"),
                "clouds": data.get("clouds", {}).get("all"),
                "timestamp": data.get("dt"),
                "sunrise": data.get("sys", {}).get("sunrise"),
                "sunset": data.get("sys", {}).get("sunset")
            }
            return result
        except requests.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return {"error": "Failed to fetch weather data", "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in weather plugin: {e}")
            return {"error": "Unexpected error", "message": str(e)}
    
    def get_forecast(self, location: str, days: int = 5) -> Optional[Dict[str, Any]]:
        """
        Get a weather forecast for a location.
        
        Args:
            location: Location to get forecast for
            days: Number of days to forecast (max 7)
            
        Returns:
            Dictionary with forecast information or None if retrieval failed
        """
        if not self.api_key:
            logger.error("API key not set for weather plugin")
            return {
                "error": "API key not configured",
                "message": "Please set the OpenWeatherMap API key in the plugin settings"
            }
        
        # Cap days at 7
        days = min(days, 7)
        
        try:
            # Use the forecast endpoint
            forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",
                "cnt": days * 8  # 8 forecasts per day (every 3 hours)
            }
            response = requests.get(forecast_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            # Process the forecast data
            forecast_list = data.get("list", [])
            result = {
                "location": data.get("city", {}).get("name"),
                "country": data.get("city", {}).get("country"),
                "forecasts": []
            }
            
            # Group forecasts by day
            day_forecasts = {}
            for forecast in forecast_list:
                # Extract date from timestamp
                timestamp = forecast.get("dt")
                date = timestamp // 86400 * 86400  # Round to beginning of day
                
                if date not in day_forecasts:
                    day_forecasts[date] = []
                
                day_forecasts[date].append({
                    "timestamp": timestamp,
                    "temperature": forecast.get("main", {}).get("temp"),
                    "feels_like": forecast.get("main", {}).get("feels_like"),
                    "humidity": forecast.get("main", {}).get("humidity"),
                    "weather": forecast.get("weather", [{}])[0].get("main"),
                    "description": forecast.get("weather", [{}])[0].get("description"),
                    "wind_speed": forecast.get("wind", {}).get("speed"),
                    "clouds": forecast.get("clouds", {}).get("all")
                })
            
            # Add days to result in chronological order
            for date in sorted(day_forecasts.keys()):
                result["forecasts"].append({
                    "date": date,
                    "entries": day_forecasts[date]
                })
            
            return result
        except requests.RequestException as e:
            logger.error(f"Error fetching forecast data: {e}")
            return {"error": "Failed to fetch forecast data", "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in weather plugin: {e}")
            return {"error": "Unexpected error", "message": str(e)}
    
    def shutdown(self) -> bool:
        """
        Shut down the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        self._is_initialized = False
        logger.info("Weather plugin shut down")
        return True
