from typing import Optional
from pydantic import BaseModel


class Account(BaseModel):
    id: str
    pwd: str
    account_nb: str
    region: Optional[str]
