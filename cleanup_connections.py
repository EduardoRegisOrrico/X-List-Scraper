#!/usr/bin/env python3
"""
Database connection cleanup script to help free up connection pool slots.
"""

import psycopg2
import os
import time
from dotenv import load_dotenv
from urllib.parse import urlparse

def get_db_params():
    """Get database connection parameters from environment."""
    load_dotenv()
    
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
            
        return conn_params
    
    # Fallback: Individual parameters (legacy XScraper format)
    user = os.getenv("user")
    password = os.getenv("password")
    host = os.getenv("host")
    port = os.getenv("port")
    dbname = os.getenv("dbname")
    
    if not all([user, password, host, port, dbname]):
        # Final fallback: SUPABASE_DATABASE_URL (old format)
        db_url = os.getenv("SUPABASE_DATABASE_URL")
        if not db_url:
            print("Error: Database connection parameters not found in .env file.")
            print("Expected: DATABASE_URL or individual parameters (user, password, host, port, dbname)")
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
            'port': int(port),
            'dbname': dbname
        }
    
    return conn_params

def show_connections():
    """Show all current connections for this user."""
    conn_params = get_db_params()
    if not conn_params:
        return False
    
    # Try using connection pooling mode instead of session mode
    conn_params_pooled = conn_params.copy()
    
    try:
        print(f"Attempting to connect to check active sessions...")
        # Try different connection approaches
        
        # First try with minimal connection params
        minimal_params = {
            'host': conn_params['host'],
            'port': conn_params['port'],
            'user': conn_params['user'],
            'password': conn_params['password'],
            'dbname': conn_params['dbname']
        }
        
        print("Trying minimal connection parameters...")
        conn = psycopg2.connect(**minimal_params)
        
        with conn.cursor() as cur:
            # Get current session info for this user
            cur.execute("""
                SELECT 
                    pid,
                    usename,
                    application_name,
                    client_addr,
                    backend_start,
                    state,
                    state_change,
                    query_start,
                    left(query, 100) as query_snippet
                FROM pg_stat_activity 
                WHERE usename = %s
                AND pid != pg_backend_pid()  -- Exclude current connection
                ORDER BY backend_start;
            """, (conn_params['user'],))
            
            sessions = cur.fetchall()
            print(f"\nFound {len(sessions)} other sessions for user '{conn_params['user']}':")
            
            if sessions:
                print("PID\t\tApp Name\t\tClient\t\tState\t\tStart Time\t\t\tState Change\t\tQuery")
                print("-" * 120)
                
                for session in sessions:
                    pid, user, app, client, start, state, state_change, q_start, query = session
                    client_str = str(client) if client else 'local'
                    app_str = str(app)[:15] if app else 'None'
                    query_str = str(query)[:50] if query else 'None'
                    print(f"{pid}\t{app_str}\t{client_str}\t{state}\t{start}\t{state_change}\t{query_str}")
                
                return sessions
            else:
                print("No other sessions found for your user.")
                return []
        
    except Exception as e:
        print(f"Error checking connections: {e}")
        return False
    finally:
        try:
            if 'conn' in locals():
                conn.close()
        except:
            pass

def wait_for_connections_to_close(timeout=60):
    """Wait for connections to close naturally."""
    print(f"\nWaiting up to {timeout} seconds for connections to close naturally...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        sessions = show_connections()
        if sessions is False:
            print("Could not check connection status")
            break
        elif len(sessions) == 0:
            print("All connections have closed!")
            return True
        else:
            print(f"Still {len(sessions)} connections open. Waiting...")
            time.sleep(5)
    
    print(f"Timeout reached. Some connections may still be open.")
    return False

def suggest_solutions():
    """Suggest solutions for connection cleanup."""
    print("\n=== SOLUTIONS TO TRY ===")
    print("1. Wait for connections to timeout naturally (may take several minutes)")
    print("2. Restart your application/service that's using the database")
    print("3. Check if you have other applications/scripts connecting to this database")
    print("4. If using Supabase, try switching connection mode:")
    print("   - Go to Supabase Dashboard > Settings > Database")
    print("   - Try changing from 'Session' to 'Transaction' pooling mode")
    print("   - Or increase the pool_size if possible")
    print("5. For immediate relief, restart the database service (if you have admin access)")
    
    print("\n=== CONNECTION STRING TIPS ===")
    print("Consider adding these parameters to your connection string:")
    print("- ?pgbouncer=true (if using PgBouncer)")
    print("- ?pool_timeout=10 (timeout for getting connection from pool)")
    print("- connection_timeout=10 (timeout for establishing connection)")

if __name__ == "__main__":
    print("=== Database Connection Cleanup Tool ===\n")
    
    # Show current connections
    sessions = show_connections()
    
    if sessions is False:
        print("Could not access database to check connections.")
        print("This might be because the pool is completely full.")
    elif len(sessions) == 0:
        print("No open connections found! You should be able to connect now.")
    else:
        print(f"\nFound {len(sessions)} open connections that might be blocking the pool.")
        
        # Ask user what they want to do
        print("\nWhat would you like to do?")
        print("1. Wait for connections to close naturally")
        print("2. Show suggestions for fixing the issue")
        print("3. Monitor connections for a while")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            wait_for_connections_to_close()
        elif choice == "2":
            suggest_solutions()
        elif choice == "3":
            print("Monitoring connections every 10 seconds. Press Ctrl+C to stop.")
            try:
                while True:
                    show_connections()
                    print("\n" + "="*50)
                    time.sleep(10)
            except KeyboardInterrupt:
                print("\nMonitoring stopped.")
        elif choice == "4":
            print("Exiting.")
        else:
            print("Invalid choice.")
    
    print("\nDone.") 