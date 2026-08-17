from app import config

from haystack.components.agents import Agent

from haystack.components.generators.chat import (
    HuggingFaceAPIChatGenerator,
)

from haystack.dataclasses import ChatMessage
from haystack.utils import Secret

from app.tools.document_tools import (
    search_document,
    get_document_info,
)


MODEL_NAME = (
    "Qwen/Qwen2.5-7B-Instruct"
)


AGENT_SYSTEM_PROMPT = """
You are a Document Intelligence Agent.

Your job is to help users understand the
currently uploaded and indexed document.

You have access to tools.

Rules:

1. If the user asks about information contained
   in the uploaded document, you MUST use the
   search_document tool before answering.

2. Use get_document_info when the user asks about
   the number of chunks, document metadata, or
   technical information about the indexed document.

3. Never invent information about the document.

4. If search_document returns no relevant results,
   clearly say that the requested information could
   not be found in the uploaded document.

5. Do not claim that you searched the document unless
   you actually called search_document.

6. Current capabilities are limited to the uploaded
   document. If the user asks for web search or data
   analysis, explain that those tools are not enabled yet.

7. Give clear, concise answers.

8. When using retrieved document evidence, mention
   the relevant source numbers when appropriate.
"""


chat_generator = HuggingFaceAPIChatGenerator(
    api_type="serverless_inference_api",

    api_params={
        "model": MODEL_NAME,
        "provider": "together",
    },

    token=Secret.from_env_var(
        "HF_TOKEN"
    ),
)


document_agent = Agent(
    chat_generator=chat_generator,

    tools=[
        search_document,
        get_document_info,
    ],

    system_prompt=AGENT_SYSTEM_PROMPT,

    exit_conditions=[
        "text"
    ],
)


document_agent.warm_up()


def run_document_agent(
    question: str,
) -> str:

    response = document_agent.run(
        messages=[
            ChatMessage.from_user(
                question
            )
        ]
    )

    final_message = response[
        "messages"
    ][-1]

    return final_message.text