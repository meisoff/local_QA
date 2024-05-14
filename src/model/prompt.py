SYSTEM_MESSAGE_PROMT = """\
This is a chat between a user and an artificial intelligence assistant. \
The assistant gives helpful, detailed, and polite answers to the user's questions based on the context. \
The assistant should also indicate when the answer cannot be found in the context."""


CONTEXT_PROMPT_EN = """\
Answer the following question using only the context below. Only include information specifically discussed.

Here are the relevant documents for the context:

{context_str}

Instruction: Based on the above documents, provide an answer for the user question below. \
Answer 'don't know' if not present in the document. Answer strictly in Russian

Question:

{question}

"""


NEW_CONTEXT_QUESTION = """\
Given the following conversation between a user and an AI assistant and a follow up question from user,
rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:\
"""

query_gen_prompt_en = """\
    "You are a skilled search query generator, dedicated to providing accurate and relevant search queries that are concise, specific, and unambiguous.\n"
    "Generate {num_queries} unique and diverse search queries, one on each line, related to the following input query:\n"
    "### Original Query: {query}\n"
    "### Please provide search queries that are:\n"
    "- Relevant to the original query\n"
    "- Well-defined and specific\n"
    "- Free of ambiguity and vagueness\n"
    "- Useful for retrieving accurate and relevant search results\n"
    "### Generated Queries:\n"
"""



