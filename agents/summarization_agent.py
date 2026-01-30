from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
)

prompt = ChatPromptTemplate.from_template("""
You are an expert at summarizing conversations clearly and concisely.

Follow these rules strictly:
• Keep the summary objective and factual
• Include only the most important points, decisions, questions, conclusions
• Preserve original meaning — do not add interpretations or opinions
• Use neutral language
• Structure logically (chronological or by topic)
• Highlight open questions, action items, unresolved issues
• Be concise: aim for 15–30% of original length unless very short
• Indicate speakers when relevant

Conversation:
{conversation}

Summary:
""")



sum_chain = prompt | llm | StrOutputParser()

def call_summarization_agent(conversation: str | list) -> str:

    if isinstance(conversation, list):
        lines = []
        for msg in conversation:
            lines.append(f"{msg.role}: {msg.content}")
        conversation_text = "\n".join(lines)
    else:
        conversation_text = str(conversation).strip()

    if not conversation_text:
        return "[No conversation provided]"

    # Invoke the agent
    result = sum_chain.invoke({
        "conversation": conversation_text,
    })
    return result
