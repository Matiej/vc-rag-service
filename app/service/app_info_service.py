import tomllib
from pathlib import Path

from app.model.app_info import AppInfo


class AppInfoService:
    def get_app_info(self):
        BASE_DIR = Path(__file__).parent.parent.parent
        pyproject_path = BASE_DIR / "pyproject.toml"
        file_opening_mode = "rb"  # read binary(bajty nie tekst)
        with open(pyproject_path, file_opening_mode) as f:
            data = tomllib.load(f)

        project = data["project"]
        app_info: AppInfo = AppInfo(
            name=project["name"],
            version=project["version"],
            description=project["description"],
            requires_python_version=project["requires-python"],
        )
        return app_info
