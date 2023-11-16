import psycopg2

def execute_sql_file(cursor, file_path):
    # Read SQL file content and execute queries
    with open(file_path, 'r') as sql_file:
        sql_queries = sql_file.read()
        cursor.execute(sql_queries)

def initialize_database():
    try:
        # Establish connection to the database
        conn = psycopg2.connect(
            "postgres://legos_user:C5zVYNrlLNN1QTZcnLR9JqncahDpRpKg@dpg-cla17u62eqrc7394na0g-a.oregon-postgres.render.com/legos"
        )
        cursor = conn.cursor()

        # Execute SQL files to create tables or insert data
        execute_sql_file(cursor, r'C:\Users\getan\Desktop\CS-367\LEGO-Starred-Sets\.devcontainer\pg_init\01_create_tables.sql')
        

        # Commit changes and close the connection
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Database initialization completed successfully.")

    except Exception as e:
        print(f"Error: {e}")
        # Handle exceptions or errors that may occur during database initialization

if __name__ == '__main__':
    initialize_database()