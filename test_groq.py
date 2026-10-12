
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
)

response = llm.invoke(
    "Explain what a banking AI agent does in one sentence."
)

print(response.content)
