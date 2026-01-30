import datetime
from langchain.tools import tool
import pytz
from .sql_agent import call_sql_agent
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
import os

load_dotenv()

@tool("database_agent",
    description=(
        "Use this tool when the user asks questions, wants to search, filter, "
        "add, update, archive or manage personal notes and tags in the database. "
        "The database contains only notes (with title, content, timestamps, archive status) "
        "and tags (many-to-many). "
        "Pass the full user question/query directly to this tool. "
        "It can run any valid SQL (SELECT, INSERT, UPDATE, DELETE, etc.) "
        "and will return the result or confirmation."
    )
)
def call_database_agent(query: str) -> str:
    result = call_sql_agent(query)
    return result


search_tool = TavilySearch(
    max_results=5,
    topic="general",
    include_answer=False,
    include_raw_content=False,
    # include_images=False,
    # include_image_descriptions=False,
    # search_depth="basic",
    # time_range="day",
    # include_domains=None,
    # exclude_domains=None
)


MAIL_ACCOUNT = os.getenv("MAIL_ACCOUNT")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

@tool("send_email",
    description=(
        "Use this tool to send an email. "
        "You need to provide the recipient's email address, subject, and body content."
    )
)
def send_email(to: str, subject: str, body: str) -> str:
    """
    Args:
        to: Recipient email address.
        subject: Subject of the email.
        body: Body content of the email.
    Returns:
        Text indicating success or failure.
    """

    try:
        msg = EmailMessage()
        msg["From"] = MAIL_ACCOUNT
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(MAIL_ACCOUNT, MAIL_PASSWORD)
            server.send_message(msg)

        return "Email sent successfully."
    except Exception as e:
        
        return f"Failed to send email: {e}"

@tool
def get_current_time(
    timezone_str: str = 'Africa/Cairo'
):
    """
Get current date and time in the specified timezone.
Args:
    timezone_str: Timezone string, e.g., 'Africa/Cairo'.
Returns:
    A dict with formatted strings.
    date: 'YYYY-MM-DD'
    time: 'HH:MM:SS ZZZ'
    full: 'YYYY-MM-DD HH:MM:SS ZZZ'
"""

    tz = pytz.timezone(timezone_str)
    now = datetime.datetime.now(tz)
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S %Z"),
        "full": now.strftime("%Y-%m-%d %H:%M:%S %Z")
}


def get_tools():
    return [call_database_agent, send_email, get_current_time, search_tool]