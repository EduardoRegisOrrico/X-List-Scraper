#!/bin/bash

# Simple Docker runner without docker-compose
# Usage: ./docker-simple.sh [COMMAND] [OPTIONS]

set -e

# Configuration
IMAGE_NAME="x-scraper"
CONTAINER_NAME="x-scraper-monitor"
DATA_DIR="$(pwd)/data"

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Default command
COMMAND=${1:-"monitor"}

case $COMMAND in
    "build")
        echo "Building X-Scraper Docker image..."
        docker build -t $IMAGE_NAME .
        ;;
    
    "login")
        echo "Running login process..."
        docker run --rm -it \
            --env-file .env \
            -e DATA_DIR=/app/data \
            -v "$DATA_DIR:/app/data" \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            -e DISPLAY=$DISPLAY \
            --net=host \
            $IMAGE_NAME python scraper.py --login
        ;;
    
    "once")
        echo "Running single scrape..."
        docker run --rm \
            --env-file .env \
            -e DATA_DIR=/app/data \
            -v "$DATA_DIR:/app/data" \
            --net=host \
            $IMAGE_NAME python scraper.py --once "${@:2}"
        ;;
    
    "monitor")
        echo "Starting monitoring service..."
        # Stop existing container if running
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
        
        # Start new container
        docker run -d \
            --name $CONTAINER_NAME \
            --restart unless-stopped \
            --env-file .env \
            -e DATA_DIR=/app/data \
            -v "$DATA_DIR:/app/data" \
            --net=host \
            --memory=2g \
            --cpus="1.0" \
            $IMAGE_NAME python scraper.py \
                --url "https://x.com/i/lists/1919380958723158457" \
                --interval 60 \
                --scrolls 2 \
                --limit 10
        
        echo "Monitor started. Use 'docker logs -f $CONTAINER_NAME' to view logs"
        ;;
    
    "stop")
        echo "Stopping monitoring service..."
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        ;;
    
    "logs")
        echo "Showing logs..."
        docker logs -f $CONTAINER_NAME
        ;;
    
    "shell")
        echo "Opening shell in container..."
        docker exec -it $CONTAINER_NAME bash
        ;;
    
    "status")
        echo "Container status:"
        docker ps -f name=$CONTAINER_NAME
        ;;
    
    "cleanup")
        echo "Cleaning up Docker resources..."
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
        docker system prune -f
        ;;
    
    *)
        echo "X-Scraper Simple Docker Management"
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
        echo "  status    Show container status"
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