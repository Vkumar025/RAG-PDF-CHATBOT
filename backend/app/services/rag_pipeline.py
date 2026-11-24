# backend/app/services/rag_pipeline.py

import os
import uuid

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

try:
    from langchain.chains import RetrievalQA
except ImportError:
    from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

from app.services.pdf_loader import load_pdf
from app.services.vector_store import (
    create_vector_store,
    clear_vector_store
)
from app.services.llm_service import get_llm


vectordb = None
active_pdf_name = None

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_pipeline_status():
    global vectordb, active_pdf_name
    return {
        "has_pdf": vectordb is not None,
        "active_pdf": active_pdf_name
    }


def clear_pdf():
    global vectordb, active_pdf_name
    vectordb = None
    active_pdf_name = None
    clear_vector_store()
    return "PDF cleared successfully. Switched to general chatbot mode."


def chat_with_llm(question: str, history=None):
    try:
        llm = get_llm()

        system_instruction = (
            "You are a helpful, knowledgeable, and friendly AI assistant. "
            "You can engage in natural conversation, explain concepts, write code, "
            "and answer general knowledge questions accurately, politely, and clearly."
        )

        messages = [SystemMessage(content=system_instruction)]

        if history and isinstance(history, list):
            for msg in history[-10:]:
                sender = msg.get("sender")
                text = msg.get("text", "")
                if not text:
                    continue
                if sender == "user":
                    messages.append(HumanMessage(content=text))
                elif sender in ("ai", "assistant"):
                    messages.append(AIMessage(content=text))

        messages.append(HumanMessage(content=question))

        response = llm.invoke(messages)
        answer = response.content if hasattr(response, "content") else str(response)

        return {
            "answer": answer,
            "sources": [],
            "mode": "general"
        }

    except Exception as e:
        print("\nCHAT ERROR:", repr(e))
        return {
            "answer": f"Error generating response: {str(e)}",
            "sources": [],
            "mode": "general"
        }


def process_pdf(file):

    global vectordb, active_pdf_name

    unique_filename = (
        f"{uuid.uuid4()}_{file.filename}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    try:

        # SAVE PDF
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        print(f"\nPDF STORED AT: {file_path}")

        # LOAD PDF
        documents = load_pdf(file_path)

        print("\nTOTAL DOCUMENTS:", len(documents))

        if not documents:
            return "No readable text found inside PDF."

        # TEXT CHUNKING
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=80,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                ""
            ]
        )

        split_docs = splitter.split_documents(documents)

        print("\nTOTAL CHUNKS:", len(split_docs))

        if not split_docs:
            return "No readable text found inside PDF."

        # CREATE VECTOR STORE
        vectordb = create_vector_store(split_docs)
        active_pdf_name = file.filename

        return "PDF uploaded successfully"

    except Exception as e:

        print("\nPDF PROCESSING ERROR:", repr(e))

        return "Error processing PDF."


def ask_question(question, history=None):

    global vectordb, active_pdf_name

    # If no PDF is uploaded, act as a normal conversational chatbot
    if vectordb is None:
        return chat_with_llm(question, history)

    try:

        # RETRIEVER
        retriever = vectordb.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 5
            }
        )

        # GROQ LLM
        llm = get_llm()

        # PROMPT
        prompt_template = """
You are a strict AI assistant.

Answer the question ONLY from the provided PDF context.

RULES:
- Do NOT use outside knowledge.
- Do NOT guess answers.
- Do NOT hallucinate.
- Carefully analyze the context.
- Keep answers concise and clear.
- If the answer is not available, reply exactly:
  "Information not found in PDF."

Context:
{context}

Question:
{question}

Answer:
"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=[
                "context",
                "question"
            ]
        )

        # RETRIEVAL QA CHAIN
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=True,
            chain_type="stuff",
            chain_type_kwargs={
                "prompt": PROMPT
            }
        )

        response = qa_chain.invoke({
            "query": question
        })

        answer = response["result"]

        source_docs = response["source_documents"]

        print("\nQUESTION:", question)
        print("\nANSWER:", answer)

        # SOURCE DOCUMENTS
        sources = []

        for i, doc in enumerate(source_docs):

            print(f"\nSOURCE {i+1}")
            print(doc.page_content[:500])

            sources.append({
                "page": doc.metadata.get(
                    "page",
                    "Unknown"
                ),
                "content": doc.page_content[:300]
            })

        return {
            "answer": answer,
            "sources": sources,
            "mode": "pdf"
        }

    except Exception as e:

        print("\nRAG ERROR:", repr(e))

        return {
            "answer": "Error generating response.",
            "sources": [],
            "mode": "pdf"
        }
