from app import config


from haystack.components.agents import (
    Agent,
)

from haystack.components.generators.chat import (
    OpenAIChatGenerator,
)

from haystack.dataclasses import (
    ChatMessage,
)

from haystack.utils import (
    Secret,
)


from app.tools.document_tools import (
    get_document_info,
    search_document,
)

from app.tools.data_tools import (
    aggregate_data,
    filter_data,
    get_data_info,
)


# =========================================================
# MODEL
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
2. A structured dataset such as CSV or XLSX.

Every request belongs to exactly one application session.

The application automatically restricts tools to the
current session.

Never ask the user for a session ID.
Never invent a session ID.
Never modify or guess session IDs.
Session isolation is handled by the application.

You MUST use the appropriate tool rather than
inventing facts or numerical results.


=========================================================
DOCUMENT TOOL: search_document
=========================================================

Use search_document when the user asks about facts,
topics, information, experience, skills, technologies,
or other content inside the PDF/document.

Examples:

- What skills are mentioned in the PDF?
- What experience does the candidate have?
- What does the report say about revenue?
- What technologies are discussed?
- Explain the project in the document.

Search the document before answering.


=========================================================
DOCUMENT TOOL: get_document_info
=========================================================

get_document_info requires a "request" argument.

Use:

request="chunk_count"

for:

- How many PDF chunks are indexed?
- How many document chunks exist?


Use:

request="metadata"

for:

- Show document metadata.
- What metadata exists?


Use:

request="summary"

for:

- Give technical information about the
  indexed document.

Never call get_document_info without "request".


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


Use:

request="column_count"

for:

- How many columns are there?


Use:

request="columns"

for:

- What columns are available?
- List the dataset columns.
- What fields exist?


Use:

request="preview"

for:

- Show the first 5 rows.
- Preview the dataset.


Use:

request="data_types"

for:

- What are the data types?
- Show column data types.


Use:

request="missing_values"

for:

- Are there missing values?
- Show missing-value counts.


Use:

request="summary"

for:

- Tell me about the dataset.
- Describe the dataset.

Never call get_data_info without "request".


=========================================================
DATA TOOL: aggregate_data
=========================================================

Use aggregate_data for mathematical calculations.

Required:

- column
- operation

Optional:

- group_by

Valid operations:

sum
mean
median
min
max
count


Examples:

What is total revenue?

aggregate_data(
    column="revenue",
    operation="sum",
    group_by=""
)


What is average revenue?

aggregate_data(
    column="revenue",
    operation="mean",
    group_by=""
)


What is total revenue by region?

aggregate_data(
    column="revenue",
    operation="sum",
    group_by="region"
)


=========================================================
DATA TOOL: filter_data
=========================================================

Use filter_data when the user asks to show,
find, select, or filter dataset rows.

Required:

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

Show West region orders.

filter_data(
    column="region",
    operator="eq",
    value="West"
)


Show revenue greater than 1000.

filter_data(
    column="revenue",
    operator="gt",
    value="1000"
)


=========================================================
ROUTING RULES
=========================================================

1. PDF content question:
   use search_document.

2. PDF chunk or metadata question:
   use get_document_info.

3. Dataset rows, columns, preview, data types,
   missing values:
   use get_data_info.

4. Dataset calculations:
   use aggregate_data.

5. Dataset filtering:
   use filter_data.

6. "Rows" and "records" mean dataset rows.

7. Never calculate dataset results yourself.

8. Never invent numerical results.

9. Never invent column names.

10. If you do not know available columns,
    use get_data_info with request="columns".

11. If a tool returns an error,
    explain the error rather than guessing.

12. Never claim that a tool ran unless it ran.

13. Do not ask for or expose internal session IDs.

14. Keep answers concise and understandable.
"""


# =========================================================
# CHAT GENERATOR
# =========================================================

chat_generator = (
    OpenAIChatGenerator(

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
)


# =========================================================
# AGENT
# =========================================================

document_agent = Agent(

    chat_generator=
        chat_generator,

    tools=[
        search_document,
        get_document_info,
        get_data_info,
        aggregate_data,
        filter_data,
    ],

    system_prompt=
        AGENT_SYSTEM_PROMPT,

    exit_conditions=[
        "text"
    ],

    # -----------------------------------------------------
    # Per-run application state
    # -----------------------------------------------------

    state_schema={

        "session_id": {
            "type": str
        }
    },
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
    session_id: str,
) -> str:
    """
    Run the Document Intelligence Agent inside
    one application session.
    """

    question = (
        question.strip()
    )


    if not question:

        raise ValueError(
            "Question cannot be empty."
        )


    if not session_id:

        raise ValueError(
            "session_id is required."
        )


    response = (
        document_agent.run(

            messages=[
                ChatMessage.from_user(
                    question
                )
            ],

            # -------------------------------------------------
            # Haystack places this inside Agent State.
            # Tools receive it automatically via State.
            # -------------------------------------------------

            session_id=
                str(session_id),
        )
    )


    messages = response.get(
        "messages",
        []
    )


    # -----------------------------------------------------
    # RETURN ONLY ASSISTANT TEXT
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

            and

            message.text
        ):

            return message.text


    return (
        "The agent could not generate "
        "a final assistant response."
    )