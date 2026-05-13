from pydantic import BaseModel, Field


class WorkdaySkillsResponse(BaseModel):
    skills: list[str] = Field(default_factory=list)
    skills_csv: str
