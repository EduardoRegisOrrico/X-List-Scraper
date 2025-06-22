#!/usr/bin/env python3
"""
Updated database connection module for XScraper to work with newsio-single database.
This version prioritizes DATABASE_URL while maintaining backward compatibility.
"""

import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv


def get_db_connection():
    """
    Establishes a PostgreSQL database connection using environment variables from .env file.
    Prioritizes DATABASE_URL (newsio-single format) but falls back to individual parameters.
    """
    load_dotenv()
    
    try:
        # First priority: DATABASE_URL (newsio-single format)
        database_url = os.getenv("DATABASE_URL")
        
        if database_url:
            print("Using DATABASE_URL connection string...")
            # Parse the DATABASE_URL
            parsed_url = urlparse(database_url)
            conn_params = {
                'dbname': parsed_url.path[1:],  # Remove leading slash
                'user': parsed_url.username,
                'password': parsed_url.password,
                'host': parsed_url.hostname,
                'port': parsed_url.port or 5432
            }
            
            # Handle query parameters (like schema)
            options = []
            if parsed_url.query:
                # Handle schema parameter if present
                if 'schema=' in parsed_url.query:
                    schema_name = parsed_url.query.split('schema=')[-1].split('&')[0]
                    options.append(f'search_path={schema_name},public')
            
            # Add IPv4 address family preference for better connection stability
            options.append('addr_type=ipv4')
            
            if options:
                conn_params['options'] = f"-c {' -c '.join(options)}"
                
        else:
            # Fallback: Individual parameters (legacy XScraper format)
            print("DATABASE_URL not found, trying individual parameters...")
            user = os.getenv("user")
            password = os.getenv("password")
            host = os.getenv("host")
            port = os.getenv("port")
            dbname = os.getenv("dbname")
            
            if not all([user, password, host, port, dbname]):
                # Final fallback: SUPABASE_DATABASE_URL (old format)
                supabase_url = os.getenv("SUPABASE_DATABASE_URL")
                if supabase_url:
                    print("Using SUPABASE_DATABASE_URL as fallback...")
                    parsed_url = urlparse(supabase_url)
                    conn_params = {
                        'dbname': parsed_url.path[1:],
                        'user': parsed_url.username,
                        'password': parsed_url.password,
                        'host': parsed_url.hostname,
                        'port': parsed_url.port or 5432
                    }
                    
                    # Handle schema if present in query
                    options = ['addr_type=ipv4']
                    if 'schema' in parsed_url.query:
                        schema_name = parsed_url.query.split('schema=')[-1].split('&')[0]
                        options.append(f'search_path={schema_name},public')
                    
                    conn_params['options'] = f"-c {' -c '.join(options)}"
                else:
                    print("Error: No database connection parameters found in .env file.")
                    print("Expected: DATABASE_URL or individual parameters (user, password, host, port, dbname)")
                    return None
            else:
                # Use individual parameters
                conn_params = {
                    'user': user,
                    'password': password,
                    'host': host,
                    'port': int(port),
                    'dbname': dbname
                }
        
        # Connect to the database
        print(f"Connecting to database at {conn_params['host']}:{conn_params['port']}...")
        print(f"Database name: {conn_params['dbname']}")
        
        conn = psycopg2.connect(**conn_params)
        
        # Test the connection
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"Successfully connected to database: {version[:50]}...")
            
        return conn
        
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        print("Please check your DATABASE_URL or individual database parameters in .env file")
        return None


if __name__ == "__main__":
    # Test the connection
    conn = get_db_connection()
    if conn:
        print("Database connection test successful!")
        conn.close()
    else:
        print("Database connection test failed!") 