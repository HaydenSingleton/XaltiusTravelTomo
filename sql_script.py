import pyodbc


# Specifying the ODBC driver, server name, database, etc. directly
conn = pyodbc.connect(
    r'DRIVER={ODBC Driver 13 for SQL Server};'
    r'SERVER=sql-stg-sc-travel.civfwvdbx0g6.ap-southeast-1.rds.amazonaws.com;'
    r'DATABASE=tripAdvisor;'
    r'UID=traveltomo;'
    r'PWD=traveltomo123'
)

# Create a cursor from the connection
cursor = conn.cursor()

# cursor.execute("""CREATE TABLE Results (
#     Title varchar(255),
#     Rating float,
#     [Review Count] int,
#     [User Reviews] varchar(255),
#     [Phone Number] varchar(255),
#     [Address] varchar(255),
#     Locality varchar(255),
#     Country varchar(255),
#     Keywords varchar(255),
#     Duration varchar(255),
#     Price varchar(255),
#     [Date Generated] varchar(255)
#     );
# """)
# conn.commit()

# cursor.execute("select user_id, user_name from users")
# row = cursor.fetchone()
# if row:
#     print(row)
