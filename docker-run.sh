#!/bin/bash

# X-Scraper Docker Runner
# Usage: ./docker-run.sh [COMMAND] [OPTIONS]

set -e

# Create data directory if it doesn't exist
mkdir -p ./data

# Detect Docker Compose command (V1 vs V2)
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "Error: Neither 'docker-compose' nor 'docker compose' is available"
    exit 1
fi

echo "Using: $DOCKER_COMPOSE"

# Default command
COMMAND=${1:-"monitor"}

case $COMMAND in
    "build")
        echo "Building X-Scraper Docker image..."
        $DOCKER_COMPOSE build
        ;;
    
    "login")
        echo "Running login process..."
        $DOCKER_COMPOSE run --rm x-scraper python scraper.py --login
        ;;
    
    "once")
        echo "Running single scrape..."
        $DOCKER_COMPOSE run --rm x-scraper python scraper.py --once "${@:2}"
        ;;
    
    "monitor")
        echo "Starting monitoring service..."
        # Ensure network exists
        if ! docker network ls | grep -q "newsio-single_newsio-network"; then
            echo "Creating Docker network..."
            docker network create newsio-single_newsio-network
        fi
        $DOCKER_COMPOSE up -d x-scraper
        echo "Monitor started. Use '$DOCKER_COMPOSE logs -f x-scraper' to view logs"
        ;;
    
    "stop")
        echo "Stopping monitoring service..."
        $DOCKER_COMPOSE down
        ;;
    
    "logs")
        echo "Showing logs..."
        $DOCKER_COMPOSE logs -f x-scraper
        ;;
    
    "shell")
        echo "Opening shell in container..."
        $DOCKER_COMPOSE exec x-scraper bash
        ;;
    
    "cleanup")
        echo "Cleaning up Docker resources..."
        $DOCKER_COMPOSE down --volumes --remove-orphans
        docker system prune -f
        ;;
    
    *)
        echo "X-Scraper Docker Management"
        echo ""
        echo "Usage: $0 [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  build     Build the Docker image"
        echo "  login     Run login process interactively"
        echo "  once      Run single scrape"
        echo "  monitor   Start monitoring service (default)"
        echo "  stop      Stop monitoring service"
        echo "  logs      Show container logs"
        echo "  shell     Open shell in container"
        echo "  cleanup   Clean up Docker resources"
        echo ""
        echo "Examples:"
        echo "  $0 build"
        echo "  $0 login"
        echo "  $0 once --limit 20"
        echo "  $0 monitor"
        echo "  $0 logs"
        ;;
esac 