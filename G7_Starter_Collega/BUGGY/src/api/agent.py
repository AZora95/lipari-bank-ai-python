from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from src.deps import Deps, get_deps

from src.agents.loop import run_agent
from src.agents.prompts import agent_system
from src.agents.tools import build_tools_for
from src.auth.deps import UserContext, get_current_user
from src.config import settings

router = APIRouter(prefix="/api/ai", tags=["ai"])


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class AgentResponse(BaseModel):
    reply: str
    steps: int
    tool_calls: list[str]


@router.post("/agent", response_model=AgentResponse)
async def agent(
    payload: AgentRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
    deps: Annotated[Deps, Depends(get_deps)],
) -> AgentResponse:
    conti = deps.accounts.ids_for(user.username)
    run = await run_agent(
        client=deps.llm,
        model=settings.llm_model,
        system_prompt=agent_system(user.username, conti),
        user_message=payload.message,
        tools=build_tools_for(user, deps),
    )
    return AgentResponse(
        reply=run.reply,
        steps=run.steps,
        tool_calls=run.tool_calls,
    )
