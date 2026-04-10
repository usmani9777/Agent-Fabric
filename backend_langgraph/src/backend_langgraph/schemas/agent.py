from pydantic import BaseModel, Field


class AgentInvokeRequest(BaseModel):
    input: str = Field(min_length=1, max_length=5000)
    refine_prompt: bool = True


class AgentInvokeResponse(BaseModel):
    refined_input: str
    selected_intent: str
    tool_context: list[str]
    memory_written: bool
    output: str
