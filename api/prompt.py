
from langchain_core.prompts import PromptTemplate

PROMPT = PromptTemplate(
    input_variables=["context", "input"],
    template="""
You are a helpful assistant. Use ONLY the provided context to answer.

Context:
{context}

Question:
{input}

If the answer is not in the context, say "I don't know".
"""
)

EXAMPLE_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
Example:
Context:
Vels University was founded in 1992 by Dr. Ishari K. Ganesh.

Question:
Who is the founder of Vels University?

Answer:
Dr. Ishari K. Ganesh

Now answer the following:

Context:
{context}

Question:
{question}

Answer:
"""
)