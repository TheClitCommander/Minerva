#!/usr/bin/env python3
"""
Minerva Full System Deployment

This script manages the full deployment of the enhanced Hugging Face functions
after successful limited testing and monitoring, including final optimization
and system-wide integration.
"""

import os
import sys
import json
import time
import shutil
import logging
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'logs', 
            f'full_deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ))
    ]
)

logger = logging.getLogger('full_deployment')

# Ensure project root is in path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

class DeploymentManager:
    """
    Manages the full deployment of enhanced Hugging Face functions across the system.
    """
    
    def __init__(self, config_file: Optional[str] = None, backup_dir: Optional[str] = None):
        """
        Initialize the deployment manager.
        
        Args:
            config_file: Path to the deployment configuration file.
            backup_dir: Directory to store backups of modified files.
        """
        self.config_file = config_file or os.path.join(project_root, "config", "deployment_config.json")
        self.backup_dir = backup_dir or os.path.join(project_root, "backups")
        self.start_time = datetime.now()
        
        # Create necessary directories
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Define key file paths
        self.key_files = {
            "app_py": os.path.join(project_root, "web", "app.py"),
            "response_handler_py": os.path.join(project_root, "web", "response_handler.py"),
            "multi_model_processor_py": os.path.join(project_root, "web", "multi_model_processor.py"),
            "integrated_huggingface_py": os.path.join(project_root, "integrated_huggingface.py")
        }
        
        logger.info(f"Deployment manager initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration from file."""
        default_config = {
            "backup_enabled": True,
            "restart_services": True,
            "optimize_performance": True,
            "verification_tests": True,
            "target_environment": "production",
            "deployment_steps": [
                "backup",
                "update_feature_flags",
                "copy_enhanced_files",
                "verify_system",
                "optimize_parameters",
                "restart_services",
                "verify_integration"
            ],
            "feature_flags": {
                "enhanced_parameter_optimization": True,
                "enhanced_response_cleaning": True,
                "enhanced_error_handling": True,
                "detailed_logging": True,
                "think_tank_integration": True
            },
            "optimization_settings": {
                "cache_enabled": True,
                "max_cache_size": 1000,
                "thread_pool_size": 8,
                "timeout_seconds": 30
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    logger.info(f"Loaded configuration from {self.config_file}")
                    return config
            else:
                # Create default config file
                with open(self.config_file, "w") as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default configuration at {self.config_file}")
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return default_config
    
    def backup_key_files(self) -> bool:
        """
        Create backups of key files before modification.
        
        Returns:
            Whether the backup was successful.
        """
        if not self.config.get("backup_enabled", True):
            logger.info("Backup disabled in configuration, skipping")
            return True
        
        logger.info("Backing up key files before deployment")
        
        # Create a timestamped backup directory
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.backup_dir, f"pre_deployment_{backup_timestamp}")
        os.makedirs(backup_dir, exist_ok=True)
        
        success = True
        for name, path in self.key_files.items():
            if os.path.exists(path):
                try:
                    backup_path = os.path.join(backup_dir, os.path.basename(path))
                    shutil.copy2(path, backup_path)
                    logger.info(f"Backed up {name} to {backup_path}")
                except Exception as e:
                    logger.error(f"Error backing up {name}: {str(e)}")
                    success = False
            else:
                logger.warning(f"File {path} does not exist, skipping backup")
        
        return success
    
    def update_feature_flags(self) -> bool:
        """
        Update feature flags in the system configuration.
        
        Returns:
            Whether the update was successful.
        """
        logger.info("Updating feature flags")
        
        try:
            # In a real system, this would update a feature flags file or database
            # For this demo, we'll just create a feature flags file
            feature_flags = self.config.get("feature_flags", {})
            feature_flags_file = os.path.join(project_root, "config", "feature_flags.json")
            
            with open(feature_flags_file, "w") as f:
                json.dump(feature_flags, f, indent=2)
            
            logger.info(f"Updated feature flags at {feature_flags_file}")
            return True
        except Exception as e:
            logger.error(f"Error updating feature flags: {str(e)}")
            return False
    
    def copy_enhanced_files(self) -> bool:
        """
        Copy enhanced implementation files to the appropriate directories.
        
        Returns:
            Whether the copy was successful.
        """
        logger.info("Copying enhanced implementation files")
        
        # Define source and destination paths
        source_files = {
            "integrated_huggingface.py": os.path.join(project_root, "integrated_huggingface.py"),
            "huggingface_integration_test.py": os.path.join(project_root, "huggingface_integration_test.py")
        }
        
        success = True
        for name, source_path in source_files.items():
            if os.path.exists(source_path):
                try:
                    # In a real system, this might involve more complex file merging or version control
                    # For this demo, we just ensure the files are in the right place
                    dest_path = os.path.join(project_root, name)
                    if source_path != dest_path:
                        shutil.copy2(source_path, dest_path)
                        logger.info(f"Copied {name} to {dest_path}")
                except Exception as e:
                    logger.error(f"Error copying {name}: {str(e)}")
                    success = False
            else:
                logger.warning(f"Source file {source_path} does not exist, skipping")
                success = False
        
        return success
    
    def verify_system(self) -> bool:
        """
        Run verification tests to confirm system integrity.
        
        Returns:
            Whether the verification was successful.
        """
        if not self.config.get("verification_tests", True):
            logger.info("Verification tests disabled in configuration, skipping")
            return True
        
        logger.info("Running system verification tests")
        
        # Run the integration tests
        test_script = os.path.join(project_root, "huggingface_integration_test.py")
        if not os.path.exists(test_script):
            logger.error(f"Test script {test_script} does not exist")
            return False
        
        try:
            logger.info(f"Running verification tests from {test_script}")
            result = subprocess.run(
                [sys.executable, test_script],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info("Verification tests passed successfully")
                return True
            else:
                logger.error(f"Verification tests failed with return code {result.returncode}")
                logger.error(f"Test output: {result.stdout}")
                logger.error(f"Test errors: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error running verification tests: {str(e)}")
            return False
    
    def optimize_parameters(self) -> bool:
        """
        Optimize system parameters based on performance data.
        
        Returns:
            Whether the optimization was successful.
        """
        if not self.config.get("optimize_performance", True):
            logger.info("Performance optimization disabled in configuration, skipping")
            return True
        
        logger.info("Optimizing system parameters")
        
        try:
            # In a real system, this would analyze performance data and adjust parameters
            # For this demo, we just update the optimization settings from the config
            optimization_settings = self.config.get("optimization_settings", {})
            optimization_file = os.path.join(project_root, "config", "optimization_settings.json")
            
            with open(optimization_file, "w") as f:
                json.dump(optimization_settings, f, indent=2)
            
            logger.info(f"Updated optimization settings at {optimization_file}")
            return True
        except Exception as e:
            logger.error(f"Error optimizing parameters: {str(e)}")
            return False
    
    def restart_services(self) -> bool:
        """
        Restart necessary services to apply changes.
        
        Returns:
            Whether the restart was successful.
        """
        if not self.config.get("restart_services", True):
            logger.info("Service restart disabled in configuration, skipping")
            return True
        
        logger.info("Restarting system services")
        
        try:
            # In a real system, this would restart the actual services
            # For this demo, we just simulate a service restart
            time.sleep(2)  # Simulate restart time
            logger.info("Services restarted successfully")
            return True
        except Exception as e:
            logger.error(f"Error restarting services: {str(e)}")
            return False
    
    def verify_integration(self) -> bool:
        """
        Verify that the deployment integrates properly with the Think Tank.
        
        Returns:
            Whether the integration verification was successful.
        """
        logger.info("Verifying Think Tank integration")
        
        # Run the Think Tank test suite
        test_script = os.path.join(project_root, "think_tank_test_suite.py")
        if not os.path.exists(test_script):
            logger.error(f"Think Tank test script {test_script} does not exist")
            return False
        
        try:
            logger.info(f"Running Think Tank tests from {test_script}")
            result = subprocess.run(
                [sys.executable, test_script],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info("Think Tank integration verified successfully")
                return True
            else:
                logger.error(f"Think Tank integration verification failed with return code {result.returncode}")
                logger.error(f"Test output: {result.stdout}")
                logger.error(f"Test errors: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error verifying Think Tank integration: {str(e)}")
            return False
    
    def execute_deployment(self) -> Dict[str, Any]:
        """
        Execute the full deployment process following the configured steps.
        
        Returns:
            Deployment results including success/failure of each step.
        """
        logger.info("Starting full deployment process")
        
        deployment_steps = self.config.get("deployment_steps", [
            "backup",
            "update_feature_flags",
            "copy_enhanced_files",
            "verify_system",
            "optimize_parameters",
            "restart_services",
            "verify_integration"
        ])
        
        results = {
            "start_time": self.start_time.isoformat(),
            "steps": {}
        }
        
        # Execute each deployment step
        all_successful = True
        for step in deployment_steps:
            logger.info(f"Executing deployment step: {step}")
            
            step_start_time = datetime.now()
            success = False
            
            try:
                if step == "backup":
                    success = self.backup_key_files()
                elif step == "update_feature_flags":
                    success = self.update_feature_flags()
                elif step == "copy_enhanced_files":
                    success = self.copy_enhanced_files()
                elif step == "verify_system":
                    success = self.verify_system()
                elif step == "optimize_parameters":
                    success = self.optimize_parameters()
                elif step == "restart_services":
                    success = self.restart_services()
                elif step == "verify_integration":
                    success = self.verify_integration()
                else:
                    logger.warning(f"Unknown deployment step: {step}")
                    success = False
            except Exception as e:
                logger.error(f"Error executing step {step}: {str(e)}")
                success = False
            
            step_end_time = datetime.now()
            step_duration = (step_end_time - step_start_time).total_seconds()
            
            results["steps"][step] = {
                "success": success,
                "start_time": step_start_time.isoformat(),
                "end_time": step_end_time.isoformat(),
                "duration_seconds": step_duration
            }
            
            if not success:
                all_successful = False
                if self.config.get("fail_fast", True):
                    logger.error(f"Deployment step {step} failed, stopping deployment")
                    break
        
        # Record overall deployment results
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = duration
        results["overall_success"] = all_successful
        
        # Save the deployment results
        results_file = os.path.join(
            project_root, 
            "logs", 
            f"deployment_results_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        try:
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Deployment results saved to {results_file}")
        except Exception as e:
            logger.error(f"Error saving deployment results: {str(e)}")
        
        return results
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """Print deployment results in a user-friendly format."""
        print("\n")
        print("="*80)
        print("FULL DEPLOYMENT RESULTS")
        print("="*80)
        
        start_time = datetime.fromisoformat(results["start_time"])
        end_time = datetime.fromisoformat(results["end_time"])
        duration = results["duration_seconds"]
        
        print(f"Started:  {start_time}")
        print(f"Finished: {end_time}")
        print(f"Duration: {int(duration // 60)} minutes, {int(duration % 60)} seconds")
        print(f"Overall:  {'✅ SUCCESS' if results['overall_success'] else '❌ FAILURE'}")
        
        print("\nDeployment Steps:")
        for step, step_results in results["steps"].items():
            status = "✅" if step_results["success"] else "❌"
            duration = step_results["duration_seconds"]
            print(f"  {status} {step:<25} - {duration:.2f}s")
        
        if results["overall_success"]:
            print("\n🎉 Deployment completed successfully! The enhanced Hugging Face functions")
            print("   are now fully deployed and operational across the system.")
        else:
            failed_steps = [step for step, step_results in results["steps"].items() if not step_results["success"]]
            print("\n❌ Deployment encountered errors in the following steps:")
            for step in failed_steps:
                print(f"   - {step}")
            print("\n   Please check the logs for detailed error information.")
        
        print("="*80)

def main():
    """Run the full deployment script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Deploy enhanced Hugging Face functions system-wide")
    parser.add_argument("--config", type=str, help="Path to the deployment configuration file")
    parser.add_argument("--backup-dir", type=str, help="Directory to store backups of modified files")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes")
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    print("="*80)
    print("MINERVA FULL SYSTEM DEPLOYMENT")
    print("="*80)
    print("Deploying enhanced Hugging Face functions system-wide")
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
    print("="*80)
    
    # Initialize deployment manager
    manager = DeploymentManager(config_file=args.config, backup_dir=args.backup_dir)
    
    if args.dry_run:
        # In dry-run mode, just print the steps that would be executed
        print("\nThe following deployment steps would be executed:")
        for i, step in enumerate(manager.config.get("deployment_steps", []), 1):
            print(f"  {i}. {step}")
        print("\nNo changes were made (dry-run mode)")
    else:
        # Execute the deployment
        results = manager.execute_deployment()
        
        # Print the results
        manager.print_results(results)

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.join(project_root, "logs"), exist_ok=True)
    
    main()
