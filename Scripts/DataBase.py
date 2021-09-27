import re
import sqlite3

conn = sqlite3.connect(f"../Discord.db")
cursor = conn.cursor()

def getDataFromDB(table: str, selectData: str, condition: str = '', type = ''):
    with conn:
        if condition == '':
            cursor.execute(f'SELECT {selectData} FROM {table}')
        else:
            cursor.execute(f'SELECT {selectData} FROM {table} WHERE {condition}')
        return ((cursor.fetchall()) if type == "all" else (cursor.fetchone()))

def updateDataInDB(table: str, updateData: str, condition: str):
    with conn: cursor.execute(f'UPDATE {table} SET {updateData} WHERE {condition}')

def deleteDataFromDB(table: str, condition: str):
    with conn: cursor.execute(f'DELETE FROM {table} WHERE {condition}')

def insertDataInDB(table: str, values: str):
    with conn: cursor.execute(f'INSERT INTO {table} VALUES ({values})')

def getTablesListFromDB():
    with conn:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return cursor.fetchall()

# async def separationOfCulumns(data: str):
#     if len(data)>1:
#         data = [str(i) for i in data]
#         return (', '.join(data))
#     else: return data