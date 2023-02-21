import mysql.connector
import pandas as pd


def get_latest_row(connection, db_table):
    cursor = connection.cursor()
    query = f"SELECT * FROM {db_table} ORDER BY id DESC LIMIT 1"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result


# database and table name
db = 'demo_rev2'
table_name = 'substation_rev2'

cnx = mysql.connector.connect(user='vmbobato',
                              password='root',
                              host='127.0.0.1',
                              database=db)

data_frame = pd.DataFrame(get_latest_row(cnx, table_name),
                          columns=["id", "time", "gen2v", "gen3", "ACEgen2",
                                   "ACEgen3", "spGen2", "spGen3"])

data_frame.to_csv("output_file2.csv", index=False)
