import logging
from dataclasses import dataclass, field

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageFunctionToolCall

from src.agents.registry import Tool

logger = logging.getLogger(__name__)


@dataclass
class AgentRun:
    """Il risultato di un'esecuzione."""

    reply: str
    steps: int = 0
    tool_calls: list[str] = field(default_factory=list)


async def run_agent(
    client: AsyncOpenAI,
    model: str,
    system_prompt: str,
    user_message: str,
    tools: list[Tool],
) -> AgentRun:
    by_name = {t.name: t for t in tools}
    schemas = [t.to_openai_schema() for t in tools]
    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    run = AgentRun(reply="")

    while True:
        run.steps += 1

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=schemas,
        )
        choice = response.choices[0].message

        if not choice.tool_calls:
            run.reply = choice.content or ""
            return run

        messages.append(choice.model_dump(exclude_none=True))

        for call in choice.tool_calls:
            run.tool_calls.append(call.function.name)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": await _execute(by_name, call),
                }
            )


async def _execute(by_name: dict[str, Tool], call: ChatCompletionMessageFunctionToolCall) -> str:
    # niente try/except: se un tool esplode vogliamo vedere l'errore vero
    tool = by_name[call.function.name]
    args = tool.args_model.model_validate_json(call.function.arguments)
    return await tool.run(args)
