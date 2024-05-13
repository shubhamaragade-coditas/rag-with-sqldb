from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.prompts.prompt import PromptTemplate
import sqlite3

load_dotenv()

try:
    llm: GoogleGenerativeAI = GoogleGenerativeAI(model='gemini-pro')
except Exception as e:
    print(f"Error initializing GoogleGenerativeAI: {e}")
    exit()

try:
    connection: sqlite3.Connection = sqlite3.connect("org.db")
    cursor: sqlite3.Cursor = connection.cursor()
    tables: sqlite3.Cursor = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
except sqlite3.Error as e:
    print(f"Error connecting to SQLite database: {e}")
    exit()

table_info: list[str] = [table[0] for table in tables]

database_info: dict = {}
for table in table_info:
    try:
        description: sqlite3.Cursor = cursor.execute(f"PRAGMA TABLE_INFO({table});")
        database_info[table] = [row for row in description]
    except sqlite3.Error as e:
        print(f"Error retrieving table info for {table}: {e}")

PROMPT: str = """
    You are an expert SQL query generator. You'll be given with the english text convert it into the sql query. The name of the database is org and has following schema:
    {schema}.\n
    Also the sql code should not have ``` in beginning or end and sql word in output. \n
    'Text' : {question}\n
    'SQL Query' : 
"""

prompt: PromptTemplate = PromptTemplate(input_variables=["schema","question"], template=PROMPT)

continue_asking: bool = True
while(continue_asking):
    try:
        question: str = input("Enter the question: ")
        query: str = prompt.template.format(schema=database_info, question=question)
        response: str = llm.invoke(query)
        response = response.replace("\n"," ")
        print("SQL query: ", response)
        cursor.execute(response)
        output: sqlite3.Cursor = cursor.fetchall()
        print("Data: ")
        for row in output:
            print(row)
    except Exception as e:
        print(f"Error executing SQL query: {e}")

    try:
        continue_asking = bool(int(input("Do you want to continue:\n 0. NO\n 1. Yes\n")))
    except ValueError:
        print("Invalid input. Exiting...")
        continue_asking = False

try:
    save_changes: bool = bool(int(input("Do you want to permanently save changes:\n 0. No\n 1. Yes\n")))
except ValueError:
    print("Invalid input. Changes will not be saved.")
    save_changes = False

if save_changes:
    try:
        connection.commit()
    except sqlite3.Error as e:
        print(f"Error committing changes to database: {e}")

connection.close()
