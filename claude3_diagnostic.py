#!/usr/bin/env python3
"""
Comprehensive diagnostic script for testing Claude-3 integration in Minerva.
Helps identify and troubleshoot common issues with API keys, environment setup,
and response handling.
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('claude3_diagnostic')

async def direct_test_anthropic(api_key, message="What is 4+4?"):
    """
    Test Anthropic API directly, bypassing Minerva's processors
    """
    try:
        import httpx
        from anthropic import AsyncAnthropic
        
        logger.info(f"🧪 Testing direct Anthropic API with query: '{message}'")
        
        # Initialize Anthropic client
        http_proxy = os.environ.get('HTTP_PROXY')
        https_proxy = os.environ.get('HTTPS_PROXY')
        
        if http_proxy or https_proxy:
            logger.info(f"Using proxy configuration: HTTP_PROXY={http_proxy}, HTTPS_PROXY={https_proxy}")
            proxies = {}
            if http_proxy:
                proxies['http://'] = http_proxy
            if https_proxy:
                proxies['https://'] = https_proxy
            
            http_client = httpx.AsyncClient(proxies=proxies)
            client = AsyncAnthropic(api_key=api_key, http_client=http_client)
        else:
            logger.info("No proxies configured, using direct connection")
            client = AsyncAnthropic(api_key=api_key)
        
        # Test with Claude-3-Haiku (most affordable option)
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[{"role": "user", "content": message}]
        )
        
        if response and hasattr(response, 'content') and response.content:
            response_text = response.content[0].text
            logger.info(f"✅ Direct API test SUCCESS. Response: {response_text}")
            return True, response_text
        else:
            logger.error("❌ Direct API test FAILED: Empty or invalid response structure")
            return False, "Empty or invalid response structure"
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Direct API test FAILED: {error_msg}")
        return False, error_msg

async def test_minerva_processor(api_key, message="What is 4+4?"):
    """
    Test Minerva's Claude-3 processor
    """
    try:
        # Import Minerva's process_with_claude3 function
        sys.path.append(str(Path(__file__).parent))
        from web.model_processors import process_with_claude3
        
        logger.info(f"🧪 Testing Minerva processor with query: '{message}'")
        
        # Set the environment variable for the API key
        os.environ["ANTHROPIC_API_KEY"] = api_key
        
        # Call the processor
        result = await process_with_claude3(message)
        
        if result.get("is_error", True):
            logger.error(f"❌ Minerva processor test FAILED: {result.get('error', 'Unknown error')}")
            return False, result
        else:
            logger.info(f"✅ Minerva processor test SUCCESS. Response: {result.get('response')[:100]}...")
            return True, result
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Minerva processor test FAILED with exception: {error_msg}")
        return False, {"error": error_msg}
    finally:
        # Clean up environment
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

async def run_diagnostics(api_key, query):
    """Run all diagnostic tests"""
    logger.info("🔍 Starting Claude-3 integration diagnostics")
    
    # Test environment
    logger.info("🧪 Checking environment...")
    python_version = sys.version
    logger.info(f"Python version: {python_version}")
    
    try:
        import anthropic
        logger.info(f"Anthropic SDK version: {anthropic.__version__}")
    except ImportError:
        logger.error("❌ Anthropic SDK not found. Please install it with: pip install anthropic")
        return
    
    # Check for existing API key in environment
    if os.environ.get("ANTHROPIC_API_KEY"):
        logger.info("⚠️ ANTHROPIC_API_KEY already set in environment. Will temporarily override.")
    
    # Run direct test
    direct_success, direct_result = await direct_test_anthropic(api_key, query)
    
    # Run processor test
    processor_success, processor_result = await test_minerva_processor(api_key, query)
    
    # Print summary
    logger.info("\n===== DIAGNOSTIC SUMMARY =====")
    logger.info(f"Direct API Test: {'✅ PASSED' if direct_success else '❌ FAILED'}")
    logger.info(f"Minerva Processor Test: {'✅ PASSED' if processor_success else '❌ FAILED'}")
    
    if not direct_success:
        logger.info("\n⚠️ Direct API test failed, which suggests issues with:")
        logger.info("   - API key validity")
        logger.info("   - Network connectivity")
        logger.info("   - Anthropic service availability")
        logger.info(f"   Error details: {direct_result}")
    
    if direct_success and not processor_success:
        logger.info("\n⚠️ Direct API works but Minerva processor failed, which suggests issues with:")
        logger.info("   - Minerva's implementation")
        logger.info("   - Incompatible client versions")
        logger.info("   - Response parsing errors")
        logger.info(f"   Error details: {processor_result.get('error', str(processor_result))}")
    
    if direct_success and processor_success:
        logger.info("\n✅ All tests PASSED! Your Claude-3 integration is working correctly.")
        logger.info("   You should be able to use Claude-3 in Minerva's Think Tank mode.")

def main():
    """Main function for the diagnostic script"""
    parser = argparse.ArgumentParser(description="Diagnose Claude-3 API integration in Minerva")
    parser.add_argument("--api-key", required=True, help="Anthropic API key")
    parser.add_argument("--query", default="What is 4+4?", help="Query to test (default: 'What is 4+4?')")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Mask API key when logging
    masked_key = args.api_key[:4] + "*" * (len(args.api_key) - 8) + args.api_key[-4:]
    logger.info(f"Using API key: {masked_key}")
    
    asyncio.run(run_diagnostics(args.api_key, args.query))

if __name__ == "__main__":
    main()
