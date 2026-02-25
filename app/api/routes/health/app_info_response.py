from pydantic import BaseModel


class AppInfoResponse(BaseModel):
    name: str
    version: str
    description: str
    requires_python_version: str

