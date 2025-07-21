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
        return "python:3.11-slim"
    
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
                """ls -la
###ACTION_DELIMITER###
make .install-deps
###ACTION_DELIMITER###
apt-get update && apt-get install -y make
###ACTION_DELIMITER###
make .install-deps
###ACTION_DELIMITER###
make .develop
###ACTION_DELIMITER###
git submodule update --init
###ACTION_DELIMITER###
make .develop
###ACTION_DELIMITER###
apt-get update && apt-get install -y nodejs npm
###ACTION_DELIMITER###
make .develop
###ACTION_DELIMITER###
echo -e 'pytest -s -v
python -X dev -m pytest -s -v -m dev_mode' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest -s -v
python -X dev -m pytest -s -v -m dev_mode

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
pytest -s -v
python -X dev -m pytest -s -v -m dev_mode

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
pytest -s -v
python -X dev -m pytest -s -v -m dev_mode

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

# Choose an appropriate base image based on the project's requirements - replace python:3.11-slim with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM python:3.11-slim

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
RUN git clone https://github.com/aio-libs/aiohttp.git /home/aiohttp

WORKDIR /home/aiohttp
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("aio-libs", "aiohttp_v3_11_0")
class AIOHTTP_V3_11_0(Instance):
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
        passed_tests = set[str]() # Tests that passed successfully
        failed_tests = set[str]() # Tests that failed
        skipped_tests = set[str]() # Tests that were skipped
        import re
        # Split log into lines
        lines = log.split('\n')
        # Compile regex patterns with case-insensitive flag (handles PASSED, passed, etc.)
        # Patterns match: [any text] test_name [separator] STATUS [any text]
        current_test = None  # Track test name across lines
        # Regex patterns optimized for common log formats
        patterns = {
            # Match test start (e.g., "Running test: test_auth.py::test_login")
            'test_start': re.compile(r'(?:Running|Executing) test: ([\w\-\.::]+)', re.IGNORECASE),
            # Match status (e.g., "Result: PASSED", "Status: [FAILED]")
            'status': re.compile(r'(?:Result|Status)[:\s]+(?:\[|\()?(PASSED|SUCCESS|OK|FAILED|ERROR|FAIL|SKIPPED|SKIP)(?:\]|\))?', re.IGNORECASE),
            # Match direct test-status pairs (e.g., "test_auth.py::test_login PASSED", "[FAILED] test_auth.py::test_login")
            'direct_status': re.compile(r'(?:([\w\-\.::]+)\s*[:\-\s]*(?:\[|\()?(PASSED|SUCCESS|OK|FAILED|ERROR|FAIL|SKIPPED|SKIP)(?:\]|\))?|(?:\[|\()?(PASSED|SUCCESS|OK|FAILED|ERROR|FAIL|SKIPPED|SKIP)(?:\]|\))?\s*[:\-\s]*([\w\-\.::]+))', re.IGNORECASE),
            # Match error traces (e.g., "File \"test_auth.py\", line 42, in test_login")
            'error_trace': re.compile(r'File ".*?", line \d+, in ([\w\-\.::]+)', re.IGNORECASE)
        }
        for line in lines:
            line = line.strip()
            # Capture test name from "Running test: X"
            if match := patterns['test_start'].search(line):
                current_test = match.group(1).strip()
            # Capture status from "Result: STATUS" and link to current_test
            elif match := patterns['status'].search(line):
                if current_test:
                    status = match.group(1).upper()
                    if status in ['PASSED', 'SUCCESS', 'OK']:
                        passed_tests.add(current_test)
                    elif status in ['FAILED', 'ERROR', 'FAIL']:
                        failed_tests.add(current_test)
                    elif status in ['SKIPPED', 'SKIP']:
                        skipped_tests.add(current_test)
                    current_test = None  # Reset after linking
            # Capture direct test-status pairs (test before/after status)
            elif match := patterns['direct_status'].search(line):
                test_name = (match.group(1) or match.group(4) or '').strip()  # Handle both test positions
                status = (match.group(2) or match.group(3) or '').upper()     # Handle both status positions
                if test_name and status:  # Ensure non-empty values
                    if status in ['PASSED', 'SUCCESS', 'OK']:
                        passed_tests.add(test_name)
                    elif status in ['FAILED', 'ERROR', 'FAIL']:
                        failed_tests.add(test_name)
                    elif status in ['SKIPPED', 'SKIP']:
                        skipped_tests.add(test_name)
            # Capture failed tests from error traces
            elif match := patterns['error_trace'].search(line):
                test_name = match.group(1).strip()
                if test_name:  # Ensure non-empty
                    failed_tests.add(test_name)
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
