#!/usr/bin/env python3
"""
Database connection diagnostic script to help identify connection leaks
and pool exhaustion issues.
"""

import psycopg2
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

def get_db_params():
    """Get database connection parameters from environment."""
    load_dotenv()
    
    user = os.getenv("user")
    password = os.getenv("password")
    host = os.getenv("host")
    port = os.getenv("port")
    dbname = os.getenv("dbname")
    
    if not all([user, password, host, port, dbname]):
        # Try the old method using SUPABASE_DATABASE_URL as fallback
        db_url = os.getenv("SUPABASE_DATABASE_URL")
        if not db_url:
            print("Error: Database connection parameters not found in .env file.")
            return None
            
        # Parse connection URL
        parsed_url = urlparse(db_url)
        conn_params = {
            'dbname': parsed_url.path[1:],
            'user': parsed_url.username,
            'password': parsed_url.password,
            'host': parsed_url.hostname,
            'port': parsed_url.port or 5432
        }
        
        # Handle schema if present in query
        options = []
        if 'schema' in parsed_url.query:
            schema_name = parsed_url.query.split('schema=')[-1].split('&')[0]
            options.append(f'search_path={schema_name},public')
        
        # Add IPv4 address family preference
        options.append('addr_type=ipv4')
        
        if options:
            conn_params['options'] = f"-c {' -c '.join(options)}"
    else:
        # Use the direct parameters from .env
        conn_params = {
            'user': user,
            'password': password,
            'host': host,
            'port': port,
            'dbname': dbname
        }
    
    return conn_params

def test_connection():
    """Test database connection and check current session info."""
    conn_params = get_db_params()
    if not conn_params:
        return False
    
    try:
        print(f"Testing connection to {conn_params['host']}:{conn_params['port']}...")
        conn = psycopg2.connect(**conn_params)
        
        with conn.cursor() as cur:
            # Get current session info
            cur.execute("""
                SELECT 
                    pid,
                    usename,
                    application_name,
                    client_addr,
                    backend_start,
                    state,
                    query_start,
                    left(query, 50) as query_snippet
                FROM pg_stat_activity 
                WHERE usename = current_user
                ORDER BY backend_start;
            """)
            
            sessions = cur.fetchall()
            print(f"\nFound {len(sessions)} sessions for current user:")
            print("PID\t\tApp Name\t\tClient\t\tState\t\tStart Time\t\tQuery")
            print("-" * 100)
            
            for session in sessions:
                pid, user, app, client, start, state, q_start, query = session
                print(f"{pid}\t{app or 'None'}\t\t{client or 'local'}\t{state}\t{start}\t{query or 'None'}")
            
            # Get connection pool info if available
            cur.execute("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity 
                WHERE usename = current_user;
            """)
            
            pool_info = cur.fetchone()
            total, active, idle = pool_info
            print(f"\nConnection Summary:")
            print(f"  Total connections: {total}")
            print(f"  Active connections: {active}")
            print(f"  Idle connections: {idle}")
            
            # Check for max connections setting
            cur.execute("SHOW max_connections;")
            max_conn = cur.fetchone()[0]
            print(f"  Max connections (server): {max_conn}")
            
        conn.close()
        print("\nConnection test successful and properly closed.")
        return True
        
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

def test_multiple_connections():
    """Test creating and cleaning up multiple connections."""
    conn_params = get_db_params()
    if not conn_params:
        return False
    
    print("\nTesting multiple connection creation and cleanup...")
    connections = []
    
    try:
        # Create 5 connections
        for i in range(5):
            try:
                conn = psycopg2.connect(**conn_params)
                connections.append(conn)
                print(f"Connection {i+1}: Created successfully")
            except Exception as e:
                print(f"Connection {i+1}: Failed - {e}")
                break
        
        print(f"Successfully created {len(connections)} connections")
        
        # Close all connections
        for i, conn in enumerate(connections):
            try:
                if not conn.closed:
                    conn.close()
                    print(f"Connection {i+1}: Closed successfully")
                else:
                    print(f"Connection {i+1}: Already closed")
            except Exception as e:
                print(f"Connection {i+1}: Error closing - {e}")
        
        print("Multiple connection test completed.")
        return True
        
    except Exception as e:
        print(f"Multiple connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Database Connection Diagnostic Tool ===\n")
    
    # Test basic connection
    if test_connection():
        print("\n" + "="*50)
        # Test multiple connections if basic test passes
        test_multiple_connections()
    else:
        print("Basic connection test failed. Cannot proceed with further tests.") 