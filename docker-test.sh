#!/bin/bash

# Quick test script to verify Docker setup and proxy rotation
set -e

echo "🐳 Testing XScraper Docker Setup"
echo "================================"

# Test 1: Build the image
echo "1. Building Docker image..."
docker build -t x-scraper-test .

# Test 2: Test proxy connections
echo "2. Testing Decodo proxy connections..."
docker run --rm --env-file .env x-scraper-test python tests/test_decodo_proxy.py

# Test 3: Test backup account switching
echo "3. Testing backup account switching..."
docker run --rm --env-file .env -v ./data:/app/data x-scraper-test python tests/test_backup_switching.py

# Test 4: Quick scrape test
echo "4. Testing single scrape..."
docker run --rm --env-file .env -v ./data:/app/data x-scraper-test python scraper.py --once --limit 5

echo "✅ All tests completed!"
echo "Your XScraper is ready for production use!"