from pydantic import BaseModel, HttpUrl
from typing import Optional

class CrawlRequest(BaseModel):
    page_url: HttpUrl
    limit: Optional[int] = 30
