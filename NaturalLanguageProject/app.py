import sqlite3
import os
from openai import OpenAI
from secrets import OPENAPI_API_KEY as key

# Load environment variables from .env

OPENAI_API_KEY = key

# Quick check
print("API Key loaded:", OPENAI_API_KEY is not None)

#initialize GPT client
client = OpenAI(api_key=OPENAI_API_KEY)

# Connect to SQLite database
conn = sqlite3.connect("university.db")
cursor = conn.cursor()

print("Connected to database!")

#get SQL from GPT
def get_sql_from_gpt(question, schema):
    prompt = f"""
        You convert English questions into SQL for SQLite.

        Follow this required format:
        1. Identify relevant tables (but DO NOT include this in the final output).
        2. Identify relevant columns (but DO NOT include this in the final output).
        3. Plan joins (but DO NOT include this in the final output).
        4. Then output ONLY the final SQL query.

        Schema:
        {schema}

        User question: {question}

        If the question contains titles such as professor or dr. treat them as a title and not as a name.

        Final answer: ONLY the SQL query.
        """
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # cheaper + fast, perfect for this
        messages=[
            {"role": "system", "content": "You are a SQL expert."},
            {"role": "user", "content": prompt}
        ]
    )
    sql_query = response.choices[0].message.content.strip()
    # Clean up markdown formatting if GPT adds code fences
    if sql_query.startswith("```"):
        sql_query = sql_query.strip("`")
        sql_query = sql_query.replace("sql", "").strip()
    return sql_query


#function to execute SQL and return data
def run_sql_query(sql_query):
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        return results
    except Exception as e:
        return f"Error: {e}"

#function to turn SQL results into plain english
def get_natural_language_answer(question, results):
    prompt = f"""
		Question: {question}
		Results: {results}
		Provide a short, natural-language answer.
		"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a friendly bakery assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    answer = response.choices[0].message.content.strip()
    return answer


#main function 
# Step 1: Define your schema
schema = """
Department (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)

Lab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    departmentID INTEGER,
    FOREIGN KEY(departmentID) REFERENCES Department(id)
)

Person (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstName TEXT NOT NULL,
    lastName TEXT NOT NULL,
    departmentID INTEGER,
    areaOfResearch TEXT,
    personType TEXT CHECK(personType IN ('professor','undergraduateStudent','graduateStudent','faculty')),
    FOREIGN KEY(departmentID) REFERENCES Department(id)
)

Building (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    constructionCompleted Date NOT NULL,
    floorCount INTEGER
)

Room (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buildingID INTEGER,
    labID INTEGER,
    roomNumber TEXT,
    FOREIGN KEY(buildingID) REFERENCES Building(id),
    FOREIGN KEY(labID) REFERENCES Lab(id)
)

PersonToLab (
    personID INTEGER,
    labID INTEGER,
    FOREIGN KEY(personID) REFERENCES Person(id),
    FOREIGN KEY(labID) REFERENCES Lab(id),
    PRIMARY KEY(personID, labID)
)
"""

# Step 2: Ask a question
question = input("Ask a question about the university's professors or research lab: ")

# Step 3: Get SQL from GPT
sql_query = get_sql_from_gpt(question, schema)
print("Generated SQL Query:\n", sql_query)

# Step 4: Run SQL
results = run_sql_query(sql_query)
print("Query Results:\n", results)

# Step 5: Get natural language answer
answer = get_natural_language_answer(question, results)
print("\nAnswer:\n", answer)

conn.close()