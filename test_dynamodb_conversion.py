#!/usr/bin/env python3

import sys
import os
from decimal import Decimal

# Add layers to path for testing
sys.path.append('layers/shared')

from job_manager import JobManager

def test_convert_for_dynamodb():
    """Test the _convert_for_dynamodb method with various data types"""
    
    # Mock environment variable
    os.environ['DYNAMODB_JOBS_TABLE'] = 'test-table'
    
    # Create JobManager instance (won't connect to real DynamoDB)
    job_manager = JobManager()
    
    # Test data with various types
    test_cases = [
        # Simple float
        (3.14, "Float conversion"),
        
        # Dictionary with floats
        ({
            "duration": 30.5,
            "size": 1024,
            "volume": 0.8,
            "name": "test"
        }, "Dict with mixed types"),
        
        # Nested dictionary
        ({
            "output": {
                "duration": 45.2,
                "size": 2048,
                "metadata": {
                    "fps": 29.97,
                    "bitrate": 1500.0
                }
            },
            "status": "completed"
        }, "Nested dict with floats"),
        
        # List with floats
        ([1.5, 2.7, 3.14, "text", 42], "List with mixed types"),
        
        # Complex nested structure
        ({
            "timeline": [
                {"start": 0.0, "volume": 0.8},
                {"start": 5.5, "volume": 1.0}
            ],
            "processing_time": 127.45,
            "metadata": {
                "fps": 30.0,
                "duration": 60.33
            }
        }, "Complex nested structure")
    ]
    
    print("Testing _convert_for_dynamodb method:")
    print("=" * 50)
    
    for i, (test_data, description) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {description}")
        print(f"Input:  {test_data}")
        
        try:
            result = job_manager._convert_for_dynamodb(test_data)
            print(f"Output: {result}")
            print(f"Types:  {_get_types(result)}")
            print("✅ PASS")
        except Exception as e:
            print(f"❌ FAIL: {e}")

def _get_types(obj):
    """Helper to show types in the converted data"""
    if isinstance(obj, dict):
        return {k: type(v).__name__ for k, v in obj.items()}
    elif isinstance(obj, list):
        return [type(item).__name__ for item in obj]
    else:
        return type(obj).__name__

def test_convert_from_dynamodb():
    """Test the _convert_from_dynamodb method with Decimal data types"""
    
    # Mock environment variable
    os.environ['DYNAMODB_JOBS_TABLE'] = 'test-table'
    
    # Create JobManager instance
    job_manager = JobManager()
    
    # Test data with Decimal types (simulating DynamoDB response)
    test_cases = [
        # Simple Decimal
        (Decimal('3.14'), "Decimal conversion"),
        
        # Dictionary with Decimals
        ({
            "duration": Decimal('30.5'),
            "size": 1024,
            "volume": Decimal('0.8'),
            "name": "test"
        }, "Dict with mixed types"),
        
        # Nested dictionary
        ({
            "output": {
                "duration": Decimal('45.2'),
                "size": 2048,
                "metadata": {
                    "fps": Decimal('29.97'),
                    "bitrate": Decimal('1500.0')
                }
            },
            "status": "completed"
        }, "Nested dict with Decimals"),
        
        # List with Decimals
        ([Decimal('1.5'), Decimal('2.7'), Decimal('3.14'), "text", 42], "List with mixed types"),
        
        # Complex nested structure
        ({
            "timeline": [
                {"start": Decimal('0.0'), "volume": Decimal('0.8')},
                {"start": Decimal('5.5'), "volume": Decimal('1.0')}
            ],
            "processing_time": Decimal('127.45'),
            "metadata": {
                "fps": Decimal('30.0'),
                "duration": Decimal('60.33')
            }
        }, "Complex nested structure")
    ]
    
    print("\nTesting _convert_from_dynamodb method:")
    print("=" * 50)
    
    for i, (test_data, description) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {description}")
        print(f"Input:  {test_data}")
        
        try:
            result = job_manager._convert_from_dynamodb(test_data)
            print(f"Output: {result}")
            print(f"Types:  {_get_types(result)}")
            print("✅ PASS")
        except Exception as e:
            print(f"❌ FAIL: {e}")

def test_round_trip_conversion():
    """Test converting to DynamoDB format and back"""
    
    # Mock environment variable
    os.environ['DYNAMODB_JOBS_TABLE'] = 'test-table'
    
    # Create JobManager instance
    job_manager = JobManager()
    
    # Original data with floats
    original_data = {
        "processingTime": 127.45,
        "output": {
            "duration": 90.2,
            "size": 15728640
        },
        "timeline": [
            {"start": 0.0, "volume": 0.8},
            {"start": 5.5, "volume": 1.0}
        ]
    }
    
    print("\nTesting round-trip conversion:")
    print("=" * 50)
    print(f"Original: {original_data}")
    print(f"Types:    {_get_types(original_data)}")
    
    # Convert to DynamoDB format
    dynamodb_data = job_manager._convert_for_dynamodb(original_data)
    print(f"\nDynamoDB: {dynamodb_data}")
    print(f"Types:    {_get_types(dynamodb_data)}")
    
    # Convert back from DynamoDB format
    converted_back = job_manager._convert_from_dynamodb(dynamodb_data)
    print(f"\nConverted back: {converted_back}")
    print(f"Types:          {_get_types(converted_back)}")
    
    # Check if data matches
    if original_data == converted_back:
        print("✅ PASS: Round-trip conversion successful")
    else:
        print("❌ FAIL: Data doesn't match after round-trip")

if __name__ == "__main__":
    test_convert_for_dynamodb()
    test_convert_from_dynamodb()
    test_round_trip_conversion()