import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from langchain_chroma import Chroma

# 1. Define the folder containing your transcripts
DATA_DIR = Path("backend/ai/rag_data/objections-v3")


# 3. Configure the text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    add_start_index=True,
)


# 4. Load, clean, and split all text files
all_chunks = []

for file_path in DATA_DIR.glob("*.json"):

    raw_text = file_path.read_text(encoding="utf-8")

    cleaned_text = raw_text

    document = Document(
        page_content=cleaned_text,
        metadata={
            "source": file_path.name,
        },
    )

    all_chunks.append(document)

    # chunks = text_splitter.split_documents([document])

# all_chunks.extend(chunks)


# 5. Inspect the results
print(f"Total chunks: {len(all_chunks)}")


embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = Chroma(
    collection_name="sales_objections",
    embedding_function=embeddings,
    persist_directory="./sales_objections_db",  # Where to save data locally, remove if not necessary
)
ids = vector_store.add_documents(documents=all_chunks)

results = vector_store.similarity_search(
    "How to handle the objkection let me think about it? answer word for word script"
)
print(results)
print(results[0])
