from pydantic import BaseModel


class AppInfo(BaseModel):
    name: str
    version: str
    description: str
    requires_python_version: str
