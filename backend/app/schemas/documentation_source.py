from pydantic import BaseModel


class DocumentationSourceCreate(BaseModel):
    name: str
    base_url: str


class DocumentationSourceResponse(BaseModel):
    id: int
    name: str
    base_url: str
    status: str

    model_config = {
        "from_attributes": True
    }