from typing import TypedDict, NotRequired, Any
import subprocess

import json
import pathlib

class Params(TypedDict):
    ipc_uri: str
    llm_api_key: str
    llm_base_url: str

class CoreLauncher:
    def __init__(self, interpreter_path: str, entry_script: str):
        self.interpreter_path = pathlib.Path(interpreter_path)
        self.entry_script = pathlib.Path(entry_script)
        self.params: Params = {
            "ipc_uri": "",
            "llm_api_key": "",
            "llm_base_url": ""
        }
    
    def ipc_uri(self, ipc_uri: str) -> "CoreLauncher":
        self.params["ipc_uri"] = ipc_uri
        return self

    def llm_api_key(self, api_key: str) -> "CoreLauncher":
        self.params["llm_api_key"] = api_key
        return self
    
    def llm_base_url(self, base_url: str) -> "CoreLauncher":
        self.params["llm_base_url"] = base_url
        return self
    
    def get_params(self) -> list[str]:
        return [f"{key}={value}" for key, value in self.params.items() if value]

    def _param_check(self) -> None:
        missing_params = [key for key, value in self.params.items() if not value and key != "extra_body"]
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

    def run(self, cwd: str | None = None, env: dict | None = None) -> subprocess.Popen:
        try:
            self._param_check()
        except ValueError as e:
            raise Exception(f"launch error: {e}") from e
        params = self.get_params()
        return subprocess.Popen([
            self.interpreter_path,
            self.entry_script,
            *params
        ],
        cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE
        )
    