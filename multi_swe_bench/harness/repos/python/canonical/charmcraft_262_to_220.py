import re
import json
from typing import Optional, Union

from multi_swe_bench.harness.image import Config, File, Image
from multi_swe_bench.harness.instance import Instance, TestResult
from multi_swe_bench.harness.pull_request import PullRequest


class ImageDefault(Image):
    def __init__(self, pr: PullRequest, config: Config):
        self._pr = pr
        self._config = config

    @property
    def pr(self) -> PullRequest:
        return self._pr

    @property
    def config(self) -> Config:
        return self._config

    def dependency(self) -> str:
        return "ubuntu:latest"
    
    def image_prefix(self) -> str:
        return "envagent"
       
    def image_tag(self) -> str:
        return f"pr-{self.pr.number}"

    def workdir(self) -> str:
        return f"pr-{self.pr.number}"

    def files(self) -> list[File]:
        return [
            File(
                ".",
                "fix.patch",
                f"{self.pr.fix_patch}",
            ),
            File(
                ".",
                "test.patch",
                f"{self.pr.test_patch}",
            ),
            File(
                ".",
                "prepare.sh",
                """apt-get update
###ACTION_DELIMITER###
apt-get install -y python3 python3-pip python3-venv
###ACTION_DELIMITER###
python3 -m venv venv
###ACTION_DELIMITER###
. venv/bin/activate
###ACTION_DELIMITER###
pip install markupsafe==2.0.1 && pip install -r requirements-dev.txt
###ACTION_DELIMITER###
echo 'python3 -m pytest -v' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
echo 'venv/bin/python3 -m pytest -v' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
venv/bin/pip install tabulate==0.9.0
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
venv/bin/pip uninstall -y urllib3 && venv/bin/pip install urllib3==1.25.11
###ACTION_DELIMITER###
ls venv/lib/python3.12/site-packages/urllib3/packages/
###ACTION_DELIMITER###
venv/bin/pip uninstall -y requests urllib3 && venv/bin/pip install requests==2.31.0 urllib3==1.26.18
###ACTION_DELIMITER###
bash test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
venv/bin/python3 -m pytest -v

""".format(
                    pr=self.pr
                ),
            ),
            File(
                ".",
                "test-run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
if ! git -C /home/{pr.repo} apply --whitespace=nowarn /home/test.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
venv/bin/python3 -m pytest -v

""".format(
                    pr=self.pr
                ),
            ),
            File(
                ".",
                "fix-run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
if ! git -C /home/{pr.repo} apply --whitespace=nowarn  /home/test.patch /home/fix.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
venv/bin/python3 -m pytest -v

""".format(
                    pr=self.pr
                ),
            ),
        ]

    def dockerfile(self) -> str:
        copy_commands = ""
        for file in self.files():
            copy_commands += f"COPY {file.name} /home/\n"

        dockerfile_content = """
# This is a template for creating a Dockerfile to test patches
# LLM should fill in the appropriate values based on the context

# Choose an appropriate base image based on the project's requirements - replace ubuntu:latest with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM ubuntu:latest

## Set noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install basic requirements
# For example: RUN apt-get update && apt-get install -y git
# For example: RUN yum install -y git
# For example: RUN apk add --no-cache git
RUN apt-get update && apt-get install -y git

# Ensure bash is available
RUN if [ ! -f /bin/bash ]; then         if command -v apk >/dev/null 2>&1; then             apk add --no-cache bash;         elif command -v apt-get >/dev/null 2>&1; then             apt-get update && apt-get install -y bash;         elif command -v yum >/dev/null 2>&1; then             yum install -y bash;         else             exit 1;         fi     fi

WORKDIR /home/
COPY fix.patch /home/
COPY test.patch /home/
RUN git clone https://github.com/canonical/charmcraft.git /home/charmcraft

WORKDIR /home/charmcraft
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("canonical", "charmcraft_262_to_220")
class CHARMCRAFT_262_TO_220(Instance):
    def __init__(self, pr: PullRequest, config: Config, *args, **kwargs):
        super().__init__()
        self._pr = pr
        self._config = config

    @property
    def pr(self) -> PullRequest:
        return self._pr

    def dependency(self) -> Optional[Image]:
        return ImageDefault(self.pr, self._config)

    def run(self, run_cmd: str = "") -> str:
        if run_cmd:
            return run_cmd

        return 'bash /home/run.sh'

    def test_patch_run(self, test_patch_run_cmd: str = "") -> str:
        if test_patch_run_cmd:
            return test_patch_run_cmd

        return "bash /home/test-run.sh"

    def fix_patch_run(self, fix_patch_run_cmd: str = "") -> str:
        if fix_patch_run_cmd:
            return fix_patch_run_cmd

        return "bash /home/fix-run.sh"


    def parse_log(self, log: str) -> TestResult:
        # Parse the log content and extract test execution results.
        passed_tests = set()  # Tests that passed successfully
        failed_tests = set()  # Tests that failed
        skipped_tests = set()  # Tests that were skipped
        import re
        # Implement the log parsing logic here
        # Regex patterns for extracting test names based on status
        passed_patterns = [
            re.compile(r'(?P<test_name>tests\/[\w\/]+\.py::[\w\+\-\[\]]+)\s+PASSED\b'),
            re.compile(r'PASSED\s+(?P<test_name>tests\/[\w\/]+\.py::[\w\+\-\[\]]+)\b')
        ]
        failed_patterns = [
            re.compile(r'(?P<test_name>tests\/[\w\/]+\.py::[\w\+\-\[\]]+)\s+FAILED\b'),
            re.compile(r'FAILED\s+(?P<test_name>tests\/[\w\/]+\.py::[\w\+\-\[\]]+)\b')
        ]
        skipped_patterns = [
            re.compile(r'(?P<test_name>tests\/[\w\/]+\.py::[\w\+\-\[\]]+)\s+(XFAIL|SKIPPED)\b'),
            re.compile(r'(XFAIL|SKIPPED)\s+(?P<test_name>tests\/[\w\/]+\.py::[\w\+\-\[\]]+)\b')
        ]
        # Extract passed tests
        for pattern in passed_patterns:
            for match in pattern.finditer(log):
                passed_tests.add(match.group('test_name'))
        # Extract failed tests
        for pattern in failed_patterns:
            for match in pattern.finditer(log):
                failed_tests.add(match.group('test_name'))
        # Extract skipped tests
        for pattern in skipped_patterns:
            for match in pattern.finditer(log):
                skipped_tests.add(match.group('test_name'))
        parsed_results = {
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests
        }
        

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
