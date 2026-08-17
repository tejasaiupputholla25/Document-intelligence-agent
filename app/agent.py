from app import config

from haystack.components.agents import Agent

from haystack.components.generators.chat import (
    HuggingFaceAPIChatGenerator,
)

from haystack.dataclasses import ChatMessage
from haystack.utils import Secret


# ---------------------------------------------------------
# PDF / document tools
# ---------------------------------------------------------

from app.tools.document_tools import (
    search_document,
    get_document_info,
)


# ---------------------------------------------------------
# Structured-data tools
# ---------------------------------------------------------

from app.tools.data_tools import (
    get_data_info,
    aggregate_data,
    filter_data,
)


# =========================================================
# MODEL
# =========================================================

MODEL_NAME = (
    "Qwen/Qwen2.5-7B-Instruct"
)


# =========================================================
# AGENT SYSTEM PROMPT
# =========================================================

AGENT_SYSTEM_PROMPT = """
You are a Document Intelligence Agent.

You can work with two types of information:

1. An uploaded unstructured document such as a PDF.
2. A loaded structured dataset such as CSV or XLSX.

You have access to several tools.


=========================================================
PDF / DOCUMENT TOOLS
=========================================================

search_document

Use this tool when the user asks about the meaning,
facts, topics, statements, experience, information,
or textual contents of the uploaded PDF/document.


get_document_info

Use this tool when the user asks about technical
information about the indexed document, such as:

- number of chunks
- document metadata
- indexed document information


=========================================================
STRUCTURED DATA TOOLS
=========================================================

get_data_info

Use this tool when the user asks about:

- dataset columns
- number of rows
- number of columns
- data types
- missing values
- dataset structure
- dataset preview


aggregate_data

Use this tool when the user requests calculations
on structured data, including:

- total
- sum
- average
- mean
- median
- minimum
- maximum
- count
- grouped calculations

Examples:

"What is total revenue?"

"What is average revenue?"

"What is revenue by region?"

"What is average cost by product?"


filter_data

Use this tool when the user asks to find, show,
select, or filter rows based on a condition.

Examples:

"Show West region orders."

"Show rows where revenue is greater than 1000."

"Find products containing Laptop."


=========================================================
IMPORTANT ROUTING RULES
=========================================================

1. For questions about the textual meaning or contents
   of the PDF/document, use search_document.

2. For PDF/document chunk count or document metadata,
   use get_document_info.

3. For questions about CSV/XLSX structure, columns,
   missing values, row count, or data types,
   use get_data_info.

4. For mathematical calculations on CSV/XLSX data,
   use aggregate_data.

5. For selecting rows from CSV/XLSX based on conditions,
   use filter_data.

6. Do not use search_document for mathematical
   aggregations on CSV/XLSX data.

7. Do not calculate structured-data answers yourself
   when an appropriate structured-data tool exists.

8. Do not invent column names.

9. If you are unsure what columns exist,
   use get_data_info first.

10. Never invent numeric results.

11. Never claim a tool was used unless it was actually
    executed.

12. If a tool returns an error, explain the error
    clearly instead of inventing a result.

13. If the requested capability is not supported by
    the available tools, explain that limitation.

14. Keep final responses clear and concise.

15. When answering from PDF retrieval results,
    mention source numbers when appropriate.
"""


# =========================================================
# CHAT GENERATOR
# =========================================================

chat_generator = HuggingFaceAPIChatGenerator(
    api_type="serverless_inference_api",

    api_params={
        "model":
            MODEL_NAME,

        "provider":
            "together",
    },

    token=Secret.from_env_var(
        "HF_TOKEN"
    ),
)


# =========================================================
# DOCUMENT INTELLIGENCE AGENT
# =========================================================

document_agent = Agent(

    chat_generator=
        chat_generator,

    tools=[
        # PDF tools
        search_document,
        get_document_info,

        # Structured-data tools
        get_data_info,
        aggregate_data,
        filter_data,
    ],

    system_prompt=
        AGENT_SYSTEM_PROMPT,

    exit_conditions=[
        "text"
    ],
)


# ---------------------------------------------------------
# Warm up
# ---------------------------------------------------------

document_agent.warm_up()


# =========================================================
# PUBLIC FUNCTION
# =========================================================

def run_document_agent(
    question: str,
) -> str:
    """
    Send a question to the Document Intelligence Agent
    and return the final text response.
    """

    response = document_agent.run(
        messages=[
            ChatMessage.from_user(
                question
            )
        ]
    )

    final_message = (
        response["messages"][-1]
    )

    return final_message.text