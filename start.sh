#!/bin/bash

# XScraper Startup Script
set -e

echo "🚀 Starting XScraper"
echo "==================="

# Create necessary directories
mkdir -p data logs debug_logs

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy env.example to .env and configure your settings"
    exit 1
fi

# Check if network exists, create if not
if ! docker network ls | grep -q "newsio-single_newsio-network"; then
    echo "📡 Creating Docker network..."
    docker network create newsio-single_newsio-network
fi

# Build and start the scraper
echo "🔨 Building XScraper..."
docker-compose build

echo "🔄 Starting XScraper monitoring..."
docker-compose up -d x-scraper

echo "✅ XScraper started successfully!"
echo ""
echo "📊 Useful commands:"
echo "  View logs:     docker-compose logs -f x-scraper"
echo "  Stop scraper:  docker-compose down"
echo "  Run tests:     docker-compose --profile testing run test-runner"
echo "  Test proxy:    docker-compose --profile testing run proxy-test"
echo ""
echo "🔍 Monitor status:"
docker-compose ps