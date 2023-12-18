import difflib
import os
import re
import subprocess

from chatdev.utils import log_and_print_online

class Containers:
    def __init__(self, generated_content=""):
        self.directory: str = None
        self.version: float = 0.0
        self.generated_content: str = generated_content
        self.codebooks = {}

        if generated_content != "":
            regex = r"(.+?)\n```Dockerfile.*?\n(.*?)```"
            matches = re.finditer(regex, self.generated_content, re.DOTALL)
            for match in matches:
                code = match.group(2)
                if "CODE" in code:
                    continue
                filename = "Dockerfile"
                self.codebooks[filename] = self._format_code(code)

    def _format_code(self, code):
        code = "\n".join([line for line in code.split("\n") if len(line.strip()) > 0])
        return code

    def _update_codes(self, generated_content):
        new_codes = Containers(generated_content)
        differ = difflib.Differ()
        for key in new_codes.codebooks.keys():
            if key not in self.codebooks.keys() or self.codebooks[key] != new_codes.codebooks[key]:
                update_codes_content = "**[Update Codes]**\n\n"
                update_codes_content += "{} updated.\n".format(key)
                old_codes_content = self.codebooks[key] if key in self.codebooks.keys() else "# None"
                new_codes_content = new_codes.codebooks[key]

                lines_old = old_codes_content.splitlines()
                lines_new = new_codes_content.splitlines()

                unified_diff = difflib.unified_diff(lines_old, lines_new, lineterm='', fromfile='Old', tofile='New')
                unified_diff = '\n'.join(unified_diff)
                update_codes_content = update_codes_content + "\n\n" + """```
'''

'''\n""" + unified_diff + "\n```"

                log_and_print_online(update_codes_content)
                self.codebooks[key] = new_codes.codebooks[key]

    def _rewrite_codes(self, git_management, phase_info=None) -> None:
        directory = self.directory
        rewrite_codes_content = "**[Rewrite Codes]**\n\n"

        for filename in self.codebooks.keys():
            filepath = os.path.join(directory, filename)
            with open(filepath, "w", encoding="utf-8") as writer:
                writer.write(self.codebooks[filename])
                rewrite_codes_content += os.path.join(directory, filename) + " Wrote\n"


    def _get_codes(self) -> str:
        content = ""
        for filename in self.codebooks.keys():
            content += "{}\n```{}\n{}\n```\n\n".format(filename,
                                                       "python" if filename.endswith(".py") else filename.split(".")[
                                                           -1], self.codebooks[filename])
        return content

    def _load_from_hardware(self, directory) -> None:
        assert len([filename for filename in os.listdir(directory) if filename.endswith(".py")]) > 0
        for root, directories, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(".py"):
                    code = open(os.path.join(directory, filename), "r", encoding="utf-8").read()
                    self.codebooks[filename] = self._format_code(code)
        log_and_print_online("{} files read from {}".format(len(self.codebooks.keys()), directory))
