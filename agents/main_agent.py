from langchain.agents import create_agent
from langchain_groq import ChatGroq
from .tools import get_tools
from langchain_core.messages import HumanMessage
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv
load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    verbose=True,
)

# llm = OllamaLLM(model="gemma:2b", temperature=0.0)  # for testing "doesn't support tools"

system_prompt = """
You are personal assistant — practical, concise, reliable.
Alwyays use tools when needed to help the user.

Help effectively and stay on topic.
"""

main_agent = create_agent(
model=llm, 
tools=get_tools(),
system_prompt=system_prompt,
)

def call_main_agent(query: str, chat_history: list) -> str:
    messages = HumanMessage(content=query)
    if len(chat_history) > 0:
        messages = chat_history + [messages]
    response = main_agent.invoke({"messages": messages})
    return response["messages"][-1].content


if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = call_main_agent(user_input, [])
        print(f"Agent: {response}")