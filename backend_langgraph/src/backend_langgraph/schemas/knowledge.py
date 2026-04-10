from pydantic import BaseModel, Field


class PdfIngestRequest(BaseModel):
    file_path: str = Field(min_length=3, max_length=2000)
    source: str = Field(default="pdf", min_length=1, max_length=120)


class PdfIngestResponse(BaseModel):
    status: str
    chunks: int
    file_name: str
