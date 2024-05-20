"""
Library of functions for handling the machine-learning tasks.
"""

import datetime
import pathlib

from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from textsgpt.mac.chat import Chat


def create_faiss_index(chat: Chat) -> FAISS:
    # split texts to be embedded in FAISS index
    texts = split_texts(chat)

    # use mini model to save time
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    if pathlib.Path(f"{chat.data_dir}/index.faiss").exists():
        print("Found an existing FAISS index.")
        faiss_index = FAISS.load_local(
            chat.data_dir, embeddings, allow_dangerous_deserialization=True
        )
        if not chat.messages.empty:
            print("Embedding new messages in FAISS index.")
            faiss_index.add_texts(texts)  # type: ignore
    else:
        print(
            f"Starting to creating FAISS index at {datetime.datetime.now()}. "
            "This can take several minutes for large chats."
        )
        faiss_index = FAISS.from_texts(texts, embeddings)  # type: ignore
        faiss_index.save_local(chat.data_dir)
        print(f"Finished creating FAISS index at{datetime.datetime.now()}.")

    return faiss_index


def split_texts(chat: Chat) -> list[str]:
    # combine sender and message into one field
    texts_series = chat.messages["sender"] + ": " + chat.messages["text"]  # type: ignore
    # remove newlines within messages
    texts_series = texts_series.apply(lambda text: " ".join(text.splitlines()))  # type: ignore
    joined_texts = "\n".join(texts_series)  # type: ignore

    # using RecursiveCharacterTextSplitter
    # TODO: split texts in a more sophisticated way, such as by time
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0,
    )
    return text_splitter.split_text(joined_texts)
