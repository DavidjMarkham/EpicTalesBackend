from typing import List
from pydantic import BaseModel

class StoryResponse(BaseModel):
    story: str
    options: List[str]