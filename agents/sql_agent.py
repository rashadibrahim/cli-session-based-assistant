from langchain_groq import ChatGroq
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from dotenv import load_dotenv
from langchain.agents import create_agent
from databases.notes_database import db
load_dotenv()



llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0.0,
    verbose=True,
)

# we take the db form the notes_database.py since the path is already set up there
# from langchain_community.utilities import SQLDatabase
# db = SQLDatabase.from_uri(NOTES_DATABASE_URL)

# print(f"Dialect: {db.dialect}")
# print(f"Available Tables: {db.get_usable_table_names()}")
# print(f"Sample Output: {db.run("SELECT * FROM Artist LIMIT 5;")}")


toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

# for tool in tools:
#   print(f"Tool Name: {tool.name} \nDescription: {tool.description}\n")

# no dml statements allowed
langchain_sql_prompt = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while
executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the tables in the database to see what you
can query. Do NOT skip this step.

Then you should query the schema of the most relevant tables.
""".format(
    dialect=db.dialect,
    top_k=5,
)

system_prompt = """
You are an expert SQL agent that can fully interact with a database.

Current database dialect: {dialect}
Default row limit (for SELECT): {top_k}

Follow this strict sequence:
1. Start by discovering available tables (use list_tables or equivalent tool)
2. Then inspect schema of relevant tables (use schema tool)
3. Generate correct {dialect} SQL for the user's request
4. Double-check syntax and logic before execution
5. Execute the query and get results
6. If error occurs → analyze it, fix the query, retry (max 3 attempts)

Allowed statements:
• SELECT (always limit to ≤ {top_k} rows unless user specifies otherwise)
• INSERT, UPDATE, DELETE (ask for any needed data from user if not provided)
• CREATE, ALTER, DROP, TRUNCATE and other DDL
• Any other valid SQL statement

After execution:
- For SELECT → return results in a clear, concise way (table format when useful)
- For DML/DDL → report number of rows affected or success message
- Always explain what was done in natural language

Current dialect: {dialect}
Start by examining the database structure.
""".format(
    dialect=db.dialect,
    top_k=5,
)


sql_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
  )

def call_sql_agent(query: str) -> str:
    response = sql_agent.invoke({"messages": [{"role": "user", "content": query}]})
    if isinstance(response, list):
        return response[0].content if response else "No response"
    return response["messages"][-1].content
