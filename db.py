import mysql.connector

def get_connection():
    return
     mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="pm",
        use_pure="True",
        charset="utf8"
    )