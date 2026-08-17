from app import config
import os
from haystack.components.builders import (
    ChatPromptBuilder,
)

from haystack.components.generators.chat import (
    HuggingFaceAPIChatGenerator,
)

from haystack.dataclasses import (
    ChatMessage,
)

from haystack.utils import Secret



from app.semantic_search import (
    search_documents,
)


MODEL_NAME = (
    "Qwen/Qwen2.5-7B-Instruct"
)


RAG_TEMPLATE = [

    ChatMessage.from_system(
        """
        You are a reliable document question-answering assistant.

        Answer the user's question using only the
        provided document context.

        Rules:

        1. Use the supplied document context as your
           source of truth.

        2. Do not invent facts, names, numbers,
           dates, or conclusions.

        3. Do not use outside knowledge to answer
           document-specific questions.

        4. If the provided context does not contain
           enough information, respond:

           "I could not find enough information in
           the uploaded document to answer that question."

        5. Keep the answer clear and concise.

        6. Cite supporting information using
           [SOURCE N].
        """
    ),

    ChatMessage.from_user(
        """
        DOCUMENT CONTEXT:

        {% for document in documents %}

        [SOURCE {{ loop.index }}]

        {{ document.content }}

        {% endfor %}


        QUESTION:

        {{ question }}


        ANSWER:
        """
    ),
]


prompt_builder = ChatPromptBuilder(
    template=RAG_TEMPLATE,

    required_variables={
        "documents",
        "question",
    },
)


generator = HuggingFaceAPIChatGenerator(
    api_type="serverless_inference_api",

    api_params={
        "model": MODEL_NAME,
        "provider": "together",
    },

    token=Secret.from_env_var(
        "HF_TOKEN"
    ),
)


def generate_answer(
    question: str,
    documents,
):

    if not documents:

        return (
            "I could not find enough information "
            "in the uploaded document to answer "
            "that question."
        )

    prompt_result = prompt_builder.run(
        documents=documents,
        question=question,
    )

    messages = prompt_result[
        "prompt"
    ]

    generation_result = generator.run(
        messages=messages
    )

    reply = generation_result[
        "replies"
    ][0]

    return reply.text


def ask_document(
    question: str,
    top_k: int = 3,
):

    documents = search_documents(
        query=question,
        top_k=top_k,
    )

    answer = generate_answer(
        question=question,
        documents=documents,
    )

    return {
        "question": question,
        "answer": answer,
        "documents": documents,
    }
