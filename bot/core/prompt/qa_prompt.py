def get_context_prompt(language: str) -> str:
    if language == "ru":
        return CONTEXT_PROMPT_RU
    return CONTEXT_PROMPT_EN


def get_system_prompt(language: str, is_rag_prompt: bool = True) -> str:
    if language == "ru":
        return SYSTEM_PROMPT_RAG_RU if is_rag_prompt else SYSTEM_PROMPT_RU
    return SYSTEM_PROMPT_RAG_EN if is_rag_prompt else SYSTEM_PROMPT_EN


SYSTEM_PROMPT_EN = """\
This is a chat between a user and an artificial intelligence assistant. \
The assistant gives helpful, detailed, and polite answers to the user's questions."""

SYSTEM_PROMPT_RAG_EN = """\
This is a chat between a user and an artificial intelligence assistant. \
The assistant gives helpful, detailed, and polite answers to the user's questions based on the context. \
The assistant should also indicate when the answer cannot be found in the context."""

CONTEXT_PROMPT_EN = """\
Here are the relevant documents for the context:

{context_str}

Instruction: Based on the above documents, provide a detailed answer for the user question below. \
Answer 'don't know' if not present in the document."""

CONDENSED_CONTEXT_PROMPT_EN = """\
Given the following conversation between a user and an AI assistant and a follow up question from user,
rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:\
"""

SYSTEM_PROMPT_RU = """\
Это чат между пользователем и помощником искусственного интеллекта. \
Ассистент дает полезные, подробные и вежливые ответы на вопросы пользователя."""

SYSTEM_PROMPT_RAG_RU = """\
Это чат между пользователем и помощником искусственного интеллекта. \
Ассистент дает полезные, подробные и вежливые ответы на вопросы пользователя, основываясь на контексте. \
Ассистент должен указывать, когда ответ не может быть найден в контексте."""

CONTEXT_PROMPT_RU = """\
Вот соответствующие документы для данного контекста:

{context_str}

Инструкция: Основываясь на вышеуказанных документах, дайте подробный ответ на вопрос пользователя, приведенный ниже. \
Ответ «не знаю», если его нет в документе."""

CONDENSED_CONTEXT_PROMPT_RU = """\
Учитывая следующий разговор между пользователем и помощником ИИ и последующий вопрос пользователя,
перефразируйте последующий вопрос, чтобы он стал отдельным вопросом.

История чата:
{chat_history}
Последующий ввод: {question}
Отдельный вопрос:\
"""