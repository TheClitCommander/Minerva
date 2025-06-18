#!/bin/bash

echo "=========================================="
echo "   Testing Minerva API Response System    "
echo "=========================================="
echo

# Test response for "who is ben dickinson"
echo "TEST 1: 'Who is Ben Dickinson?'"
curl -s -X POST -H "Content-Type: application/json" -d '{"message":"Who is Ben Dickinson?"}' http://localhost:5505/api/chat | jq .
echo
echo

# Test response for "what is minerva"
echo "TEST 2: 'What is Minerva?'"
curl -s -X POST -H "Content-Type: application/json" -d '{"message":"What is Minerva?"}' http://localhost:5505/api/chat | jq .
echo
echo

# Test response for "hello"
echo "TEST 3: 'Hello'"
curl -s -X POST -H "Content-Type: application/json" -d '{"message":"Hello"}' http://localhost:5505/api/chat | jq .
echo
echo

# Test response for a random query
echo "TEST 4: 'Tell me about cosmic energy'"
curl -s -X POST -H "Content-Type: application/json" -d '{"message":"Tell me about cosmic energy"}' http://localhost:5505/api/chat | jq .
echo
echo

echo "=========================================="
echo "          Tests Completed                "
echo "==========================================" 