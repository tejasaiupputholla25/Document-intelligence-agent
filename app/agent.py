from app import config

from haystack.components.agents import Agent

from haystack.components.generators.chat import (
    OpenAIChatGenerator,
)

from haystack.dataclasses import (
    ChatMessage,
)

from haystack.utils import (
    Secret,
)


# =========================================================
# DOCUMENT TOOLS
# =========================================================

from app.tools.document_tools import (
    search_document,
    get_document_info,
)


# =========================================================
# DATA TOOLS
# =========================================================

from app.tools.data_tools import (
    get_data_info,
    aggregate_data,
    filter_data,
)


# =========================================================
# AGENT MODEL
# =========================================================

AGENT_MODEL_NAME = (
    "Qwen/Qwen2.5-72B-Instruct:novita"
)


# =========================================================
# SYSTEM PROMPT
# =========================================================

AGENT_SYSTEM_PROMPT = """
You are a Document Intelligence Agent.

The application can contain two types of information:

1. An indexed PDF or other unstructured document.
2. A loaded structured dataset such as CSV or XLSX.

You have tools for retrieving document information
and analyzing structured data.

You MUST use the appropriate tool instead of
inventing information.


=========================================================
DOCUMENT TOOL: search_document
=========================================================

Use search_document when the user asks about
information contained inside the uploaded PDF/document.

Examples:

- What skills are mentioned in the PDF?
- What experience does the candidate have?
- What does the report say about revenue?
- What technologies are discussed?
- Explain the project described in the document.

For document-content questions, search the document
before answering.


=========================================================
DOCUMENT TOOL: get_document_info
=========================================================

get_document_info requires a "request" argument.

Use:

request="chunk_count"

for:

- How many PDF chunks are indexed?
- How many document chunks are stored?


Use:

request="metadata"

for:

- What document metadata exists?
- Show PDF metadata.


Use:

request="summary"

for:

- Give technical information about the indexed PDF.
- Describe the indexed document state.

NEVER call get_document_info without a request argument.


=========================================================
DATA TOOL: get_data_info
=========================================================

get_data_info requires a "request" argument.

Use:

request="row_count"

for:

- How many rows are there?
- How many records are there?
- How many records are in the dataset?
- How many rows are in our file?


Use:

request="column_count"

for:

- How many columns are there?
- What is the number of columns?


Use:

request="columns"

for:

- What columns are available?
- List the dataset columns.
- What fields exist in the dataset?


Use:

request="preview"

for:

- Show the first 5 rows.
- Print the first 5 rows.
- Preview the dataset.


Use:

request="data_types"

for:

- What are the data types?
- Show the column data types.


Use:

request="missing_values"

for:

- Are there missing values?
- How many missing values are there?


Use:

request="summary"

for:

- Tell me about the dataset.
- Describe the dataset.
- Give me general information about this file.

NEVER call get_data_info without a request argument.


=========================================================
DATA TOOL: aggregate_data
=========================================================

Use aggregate_data for mathematical calculations
on structured data.

The tool requires:

- column
- operation

and optionally:

- group_by


Use these operation values:

sum
mean
median
min
max
count


Examples:


User:

What is total revenue?

Call approximately:

aggregate_data(
    column="revenue",
    operation="sum",
    group_by=""
)


User:

What is average revenue?

Call approximately:

aggregate_data(
    column="revenue",
    operation="mean",
    group_by=""
)


User:

What is total revenue by region?

Call approximately:

aggregate_data(
    column="revenue",
    operation="sum",
    group_by="region"
)


User:

What is maximum cost?

Call approximately:

aggregate_data(
    column="cost",
    operation="max",
    group_by=""
)


=========================================================
DATA TOOL: filter_data
=========================================================

Use filter_data when the user asks to find,
show, select, or filter dataset rows.

The tool requires:

- column
- operator
- value


Valid operators:

eq
ne
gt
gte
lt
lte
contains


Examples:


User:

Show West region orders.

Call approximately:

filter_data(
    column="region",
    operator="eq",
    value="West"
)


User:

Show rows where revenue is greater than 1000.

Call approximately:

filter_data(
    column="revenue",
    operator="gt",
    value="1000"
)


User:

Find products containing Laptop.

Call approximately:

filter_data(
    column="product",
    operator="contains",
    value="Laptop"
)


=========================================================
GENERAL ROUTING RULES
=========================================================

1. Questions about facts inside the PDF:
   use search_document.

2. Questions about PDF chunks or metadata:
   use get_document_info.

3. Questions about dataset rows, records,
   columns, preview, missing values or data types:
   use get_data_info.

4. "Records" and "rows" mean dataset rows.

5. Dataset calculations:
   use aggregate_data.

6. Dataset row filtering:
   use filter_data.

7. Do not calculate structured-data results yourself.

8. Do not invent column names.

9. If you do not know the dataset column names,
   call get_data_info with request="columns" first.

10. Never invent numerical results.

11. Never claim that a tool ran unless it actually ran.

12. When calling get_data_info,
    ALWAYS provide the request argument.

13. When calling get_document_info,
    ALWAYS provide the request argument.

14. If a tool returns an error,
    explain that error instead of guessing.

15. If a requested operation is unsupported,
    explain the limitation clearly.

16. Keep final answers concise and understandable.
"""


# =========================================================
# CHAT GENERATOR
# =========================================================
#
# Important:
#
# This uses Haystack's OpenAI-compatible generator,
# but the endpoint is Hugging Face's router.
#
# HF_TOKEN is still the API credential.
# =========================================================

chat_generator = OpenAIChatGenerator(

    api_key=
        Secret.from_env_var(
            "HF_TOKEN"
        ),

    api_base_url=(
        "https://router.huggingface.co/v1"
    ),

    model=
        AGENT_MODEL_NAME,
)


# =========================================================
# AGENT
# =========================================================

document_agent = Agent(

    chat_generator=
        chat_generator,

    tools=[

        # ---------------------------------------------
        # PDF/document tools
        # ---------------------------------------------

        search_document,
        get_document_info,

        # ---------------------------------------------
        # Structured-data tools
        # ---------------------------------------------

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


# =========================================================
# WARM UP
# =========================================================

document_agent.warm_up()


# =========================================================
# RUN AGENT
# =========================================================

def run_document_agent(
    question: str,
) -> str:
    """
    Run the Document Intelligence Agent.

    Return only assistant-generated text.
    Never accidentally return the original
    user's question.
    """

    response = (
        document_agent.run(
            messages=[
                ChatMessage.from_user(
                    question
                )
            ]
        )
    )

    messages = response.get(
        "messages",
        []
    )

    # -----------------------------------------------------
    # Search backward through the conversation.
    #
    # Only ASSISTANT messages are eligible.
    #
    # This prevents the previous bug where
    # the user's question was returned as
    # the answer.
    # -----------------------------------------------------

    for message in reversed(
        messages
    ):

        role_value = (
            message.role.value
            if hasattr(
                message.role,
                "value"
            )
            else str(
                message.role
            )
        )

        if (
            role_value == "assistant"
            and message.text
        ):

            return message.text

    return (
        "The agent could not generate "
        "a final assistant response."
    )