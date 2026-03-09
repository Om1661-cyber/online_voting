import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="omsonawane16611661",
    database="onlinevoting"
)

print("Connected Successfully 👍")
conn.close()