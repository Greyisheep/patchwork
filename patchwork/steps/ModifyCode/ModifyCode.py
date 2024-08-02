import os
from patchwork.logger import logger
from patchwork.step import Step

def save_file_contents(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)

def create_test_file(original_file_path, test_content):
    dir_path, file_name = os.path.split(original_file_path)
    test_file_name = f"test_{file_name}"
    test_file_path = os.path.join(dir_path, test_file_name)
    
    with open(test_file_path, "w") as file:
        file.write(test_content)
    
    return test_file_path

class ModifyCode(Step):
    UPDATED_SNIPPETS_KEY = "extracted_responses"
    FILES_TO_PATCH = "files_to_patch"
    required_keys = {FILES_TO_PATCH, UPDATED_SNIPPETS_KEY}

    def __init__(self, inputs: dict):
        logger.info(f"Run started {self.__class__.__name__}")

        if not all(key in inputs.keys() for key in self.required_keys):
            raise ValueError(f'Missing required data: "{self.required_keys}"')

        self.files_to_patch = inputs[self.FILES_TO_PATCH]
        self.extracted_responses = inputs[self.UPDATED_SNIPPETS_KEY]
        self.mode = inputs.get("mode", "readme")

    def run(self) -> dict:
        if self.mode == "readme":
            return self._handle_readme_mode()
        elif self.mode == "unit_tests":
            return self._handle_unit_tests_mode()
        else:
            raise ValueError(f"Unsupported mode: {self.mode}")

    def _handle_readme_mode(self) -> dict:
        modified_code_files = []
        for code_snippet, extracted_response in zip(self.files_to_patch, self.extracted_responses):
            uri = code_snippet["uri"]
            new_content = extracted_response.get("patch")
            if new_content is None or new_content == "":
                continue

            save_file_contents(uri, new_content)
            modified_code_file = dict(path=uri, **extracted_response)
            modified_code_files.append(modified_code_file)

        logger.info(f"Run completed {self.__class__.__name__} in readme mode")
        return dict(modified_code_files=modified_code_files)

    def _handle_unit_tests_mode(self) -> dict:
        created_test_files = []
        for code_snippet, extracted_response in zip(self.files_to_patch, self.extracted_responses):
            original_file_path = code_snippet["uri"]
            new_test_code = extracted_response.get("patch")
            if new_test_code is None or new_test_code == "":
                continue

            test_file_path = create_test_file(original_file_path, new_test_code)
            created_test_file = dict(
                original_path=original_file_path,
                test_path=test_file_path,
                **extracted_response
            )
            created_test_files.append(created_test_file)

        logger.info(f"Run completed {self.__class__.__name__} in unit tests mode")
        return dict(created_test_files=created_test_files)