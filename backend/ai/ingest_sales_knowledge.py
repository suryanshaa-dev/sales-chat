import json
import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

KNOWLEDGE_DIR = Path("backend/ai/rag_data/sales_knowledge")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=200,
    add_start_index=True,
)


def timestamp_to_seconds(timestamp: str) -> int:
    parts = list(map(int, timestamp.split(":")))

    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds

    hours, minutes, seconds = parts
    return hours * 3600 + minutes * 60 + seconds


def extract_chapter_text(
    transcript: str,
    start_time: str,
    end_time: str,
) -> str:

    start_seconds = timestamp_to_seconds(start_time)
    end_seconds = timestamp_to_seconds(end_time)

    lines = []

    for line in transcript.splitlines():

        match = re.match(
            r"\((\d+:\d+(?::\d+)?)\)\s*(.*)",
            line,
        )

        if not match:
            continue

        timestamp = match.group(1)
        content = match.group(2)

        seconds = timestamp_to_seconds(timestamp)

        if start_seconds <= seconds < end_seconds:
            lines.append(content)

    return "\n".join(lines)


all_chunks = []

for file_path in KNOWLEDGE_DIR.glob("*.json"):

    data = json.loads(file_path.read_text(encoding="utf-8"))

    transcript = data["transcript"]

    for chapter in data["chapters"]:

        chapter_text = extract_chapter_text(
            transcript=transcript,
            start_time=chapter["start_time"],
            end_time=chapter["end_time"],
        )

        document = Document(
            page_content=chapter_text,
            metadata={
                "source": file_path.name,
                "chapter_name": chapter["chapter_name"],
                "start_time": chapter["start_time"],
                "end_time": chapter["end_time"],
            },
        )

        all_chunks.append(document)

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorStore = Chroma(
    collection_name="sales_knowledge",
    embedding_function=embeddings,
    persist_directory="./sales_knowledge_db",
)

vectorStore.add_documents(all_chunks)

print(f"Total chunks: {len(all_chunks)}")
