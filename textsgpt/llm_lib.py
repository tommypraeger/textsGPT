"""
Library of functions related to working with large language models.
"""

import datetime
import pathlib
import time

import pandas as pd
from dotenv import load_dotenv
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI

from textsgpt.mac.chat import Chat

# make sure to set OPENAI_API_KEY environment variable
load_dotenv()
client = OpenAI()


def gpt_completion(
    query: str,
    vector_index: FAISS,
    model: str = "gpt-3.5-turbo-0125",
    temperature: float = 0.7,
    frequency_penalty: float = 0.3,
    max_tokens: int = 500,
) -> str:
    """
    Feeds a query and context to a generative pre-trained transformer and returns the response.

    Args:
        query (str):
            The question to ask the GPT.
        vector_index (FAISS):
            A pre-built FAISS index used to search documents relevant to the query.
        model (str):
            The OpenAI language model to use. Defaults to gpt-3.5-turbo-0125.
        temperature (float):
            Number between 0 and 2. Defaults to 0.7.
            What sampling temperature to use. Higher values will make the output more random,
            while lower values will make it more focused and deterministic.
            Reference:
            https://platform.openai.com/docs/api-reference/chat/create#chat-create-temperature
        frequency_penalty (float):
            Number between -2.0 and 2.0. Defaults to 0.3.
            Positive values penalize new tokens based on their existing frequency
            in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
            Reference:
            https://platform.openai.com/docs/api-reference/chat/create#chat-create-frequency_penalty
        max_tokens (int):
            The maximum number of tokens that can be generated in the chat completion.
            Defaults to 500.

    Returns:
        str:
            Response from GPT.
            If there is an error, returns the error message.
    """
    context = generate_context(query, vector_index)

    max_retries = 3
    retries = 0
    while True:
        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant designed to respond to a question "
                            "based on the context provided. "
                            "The context will be in the form of multiple series of text messages. "
                            "If you don't know the answer based on the context, "
                            "say you don't know and make an inference based on your prior knowledge."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (f"Context:\n{context}\n\n" f"Question: {query}"),
                    },
                ],
                model=model,
                temperature=temperature,
                frequency_penalty=frequency_penalty,
                max_tokens=max_tokens,
            )
            text: str | None = response.choices[0].message.content
            if text is None:
                return "Did not get a valid response from GPT."
            return text.strip()
        except Exception as e:  # pylint: disable=broad-exception-caught
            retries += 1
            if retries >= max_retries:
                return f"Error communicating with OpenAI: {str(e)}"
            print(f"Error communicating with OpenAI: {str(e)}")
            time.sleep(1)


def generate_context(query: str, vector_index: FAISS, num_documents: int = 10) -> str:
    """
    Args:
        query (str):
            The question to find similar documents to.
        vector_index (FAISS):
            A pre-built FAISS index used to search for similar documents.
        num_documents (int):
            How many documents should be retrieved. Default to 10.

    Returns:
        str:
            List of similar documents concatenated into a single string.
    """
    docs = vector_index.similarity_search(query, k=num_documents)  # type: ignore
    context = "\n###\n".join(doc.page_content for doc in docs)
    return context


def create_faiss_index(chat: Chat, embedding_model: str = "all-MiniLM-L6-v2") -> FAISS:
    """
    Create a FAISS index that embeds messages in chat.
    If a FAISS index already exists for this chat, add messages into the FAISS index.

    Args:
        chat (Chat):
            The chat containing messages that should be embedded into a FAISS index.
            The chat also defines where its data (such as the FAISS index) should be preserved.
        embedding_model (str):
            Model to use to generate embeddings used when building the FAISS index.
            Defaults to all-MiniLM-L6-v2.

    Returns:
        FAISS:
            FAISS index that embeds messages of the chat.
    """
    # split texts to be embedded in FAISS index
    texts = split_texts(chat.messages)

    # use mini model to save time
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

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


def split_texts(messages: pd.DataFrame) -> list[str]:
    """
    Split texts into chunks to be embedded into the FAISS index.

    Args:
        messages (pandas.DataFrame):
            The chat containing the messages.

    Returns:
        list[str]:
            Chunks of messages.
    """
    # combine sender and message into one field
    texts_series = messages["sender"] + ": " + messages["text"]  # type: ignore
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
