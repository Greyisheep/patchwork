import os
import subprocess
from pathlib import Path

from patchwork.logger import logger
from patchwork.step import Step

FOLDER_PATH = "folder_path"

class CallCode2Prompt(Step):
    required_keys = {FOLDER_PATH}

    def __init__(self, inputs: dict):
        logger.info(f"Run started {self.__class__.__name__}")

        if not all(key in inputs.keys() for key in self.required_keys):
            raise ValueError(f'Missing required data: "{self.required_keys}"')

        self.folder_path = inputs[FOLDER_PATH]
        self.filter = inputs.get("filter", None)
        self.suppress_comments = inputs.get("suppress_comments", False)
        self.mode = inputs.get("mode", "readme")
        self.extracted_data = []

    def run(self) -> dict:
        cmd = [
            "code2prompt",
            "--path",
            self.folder_path,
        ]

        if self.filter is not None:
            cmd.extend(["--filter", self.filter])

        if self.suppress_comments:
            cmd.append("--suppress-comments")

        p = subprocess.run(cmd, capture_output=True, text=True)
        prompt_content_md = p.stdout

        if self.mode == "readme":
            return self._handle_readme_mode(prompt_content_md)
        elif self.mode == "unit_tests":
            return self._handle_unit_tests_mode()
        else:
            raise ValueError(f"Unsupported mode: {self.mode}")

    def _handle_readme_mode(self, prompt_content_md):
        readme_path = str(Path(self.folder_path) / "README.md")
        
        if not os.path.exists(readme_path):
            with open(readme_path, "a") as file:
                pass

        try:
            with open(readme_path, "r") as file:
                file_content = file.read()
        except FileNotFoundError:
            logger.info(f"README.md file not found in : {readme_path}")
            file_content = ""

        lines = file_content.splitlines(keepends=True)

        data = {
            "fullContent": prompt_content_md,
            "uri": readme_path,
            "startLine": 0,
            "endLine": len(lines)
        }
        self.extracted_data.append(data)

        return dict(files_to_patch=self.extracted_data)

    def _handle_unit_tests_mode(self):
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                if self._should_process_file(file):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    data = {
                        "fullContent": content,
                        "uri": file_path,
                        "startLine": 0,
                        "endLine": len(content.splitlines())
                    }
                    self.extracted_data.append(data)

        return dict(files_to_patch=self.extracted_data)

    def _should_process_file(self, filename):
        return filename.endswith('.py') and not filename.startswith('test_')