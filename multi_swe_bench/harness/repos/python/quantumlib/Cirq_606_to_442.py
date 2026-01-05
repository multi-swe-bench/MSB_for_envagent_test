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
        return "python:3.10-slim"
    
    def image_prefix(self) -> str:
        return "envagent"
       
    def image_tag(self) -> str:
        return f"pr-{self.pr.number}"

    def workdir(self) -> str:
        return f"pr-{self.pr.number}"

    def files(self) -> list[File]:
        repo_name= self.pr.repo
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
                """
###ACTION_DELIMITER###
ls -la
###ACTION_DELIMITER###
cat apt-runtime-requirements.txt
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
apt-get install -y $(cat apt-runtime-requirements.txt)
###ACTION_DELIMITER###
cat apt-dev-requirements.txt
###ACTION_DELIMITER###
apt-get install -y protobuf-compiler
###ACTION_DELIMITER###
cat dev-requirements.txt
###ACTION_DELIMITER###
cat runtime-requirements.txt
###ACTION_DELIMITER###
pip install --upgrade pip setuptools wheel
###ACTION_DELIMITER###
pip install -r dev-requirements.txt
###ACTION_DELIMITER###
export PATH="$HOME/.pyenv/bin:$PATH" && eval "$(pyenv init -)" && pyenv --version
###ACTION_DELIMITER###
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
###ACTION_DELIMITER###
export PATH="$HOME/.pyenv/bin:$PATH" && eval "$(pyenv init -)" && pyenv --version
###ACTION_DELIMITER###
pyenv install 3.6.15
###ACTION_DELIMITER###
apt-get install -y wget
###ACTION_DELIMITER###
pyenv install 3.6.15
###ACTION_DELIMITER###
apt-get install -y gcc
###ACTION_DELIMITER###
pyenv install 3.6.15
###ACTION_DELIMITER###
apt-get install -y make
###ACTION_DELIMITER###
pyenv install 3.6.15
###ACTION_DELIMITER###
apt-get install -y libbz2-dev libncurses5-dev libncursesw5-dev libreadline-dev libssl-dev
###ACTION_DELIMITER###
pyenv install 3.6.15
###ACTION_DELIMITER###
apt-get install -y libsqlite3-dev liblzma-dev
###ACTION_DELIMITER###
pyenv install --force 3.6.15
###ACTION_DELIMITER###
pyenv local 3.6.15 && python --version
###ACTION_DELIMITER###
pip install --upgrade pip setuptools wheel
###ACTION_DELIMITER###
pip install -r dev-requirements.txt
###ACTION_DELIMITER###
pytest --version
###ACTION_DELIMITER###
ls -la cirq/
###ACTION_DELIMITER###
ls -la cirq/testing/
###ACTION_DELIMITER###
ls -la cirq/circuits/
###ACTION_DELIMITER###
pytest -v cirq/
###ACTION_DELIMITER###
export MPLBACKEND=Agg && pytest -v cirq/
###ACTION_DELIMITER###
echo 'export MPLBACKEND=Agg && pytest -v cirq/' > /home/Cirq/test_commands.sh
###ACTION_DELIMITER###
cat /home/Cirq/test_commands.sh
###ACTION_DELIMITER###

###ACTION_DELIMITER###

###ACTION_DELIMITER###

###ACTION_DELIMITER###
"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
export MPLBACKEND=Agg && pytest -v cirq/

""".replace("[[REPO_NAME]]", repo_name)
            ),
            File(
                ".",
                "test-run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
if ! git -C /home/[[REPO_NAME]] apply --whitespace=nowarn /home/test.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
export MPLBACKEND=Agg && pytest -v cirq/

""".replace("[[REPO_NAME]]", repo_name)
            ),
            File(
                ".",
                "fix-run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
if ! git -C /home/[[REPO_NAME]] apply --whitespace=nowarn  /home/test.patch /home/fix.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
export MPLBACKEND=Agg && pytest -v cirq/

""".replace("[[REPO_NAME]]", repo_name)
            ),
        ]

    def dockerfile(self) -> str:
        copy_commands = ""
        for file in self.files():
            copy_commands += f"COPY {file.name} /home/\n"

        dockerfile_content = """
# This is a template for creating a Dockerfile to test patches
# LLM should fill in the appropriate values based on the context

# Choose an appropriate base image based on the project's requirements - replace [base image] with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM python:3.10-slim

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
RUN git clone https://github.com/quantumlib/Cirq.git /home/Cirq

WORKDIR /home/Cirq
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("quantumlib", "Cirq_606_to_442")
class CIRQ_606_TO_442(Instance):
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
        passed_tests: set[str] = set() # Tests that passed successfully
        failed_tests: set[str] = set() # Tests that failed
        skipped_tests: set[str] = set() # Tests that were skipped
        import re
        import json
        # Regex patterns: handle single-line (test+status) and multi-line (test then status)
        # Pattern 1: Single-line test entry (test name + status)
        single_line_pattern = re.compile(r'^\s*([^\n]+::[^\n]+)\s+([A-Z]+)(?:\s+\[.*\])?$')
        # Pattern 2: Test name without status (pending for subsequent status line)
        test_name_pattern = re.compile(r'^\s*([^\n]+::[^\n]+)\s*$')
        # Pattern 3: Status line (to assign to pending test name)
        status_pattern = re.compile(r'^\s*([A-Z]+)(?:\s+\[.*\])?$')
        pending_test = None
        # Split log into lines and process each
        for line in log.split('\n'):
            line = line.rstrip() # Remove trailing whitespace (including \r)
            if not line:
                continue
            # Handle single-line test entry first
            single_line_match = single_line_pattern.match(line)
            if single_line_match:
                test_name = single_line_match.group(1)
                status = single_line_match.group(2)
                if status == 'PASSED':
                    passed_tests.add(test_name)
                elif status == 'FAILED':
                    failed_tests.add(test_name)
                pending_test = None
                continue
            # Handle pending test name + subsequent status line
            if pending_test is None:
                # Check if line is a test name without status
                test_match = test_name_pattern.match(line)
                if test_match:
                    pending_test = test_match.group(1)
            else:
                # Check if line is a status for the pending test
                status_match = status_pattern.match(line)
                if status_match:
                    status = status_match.group(1)
                    if status == 'PASSED':
                        passed_tests.add(pending_test)
                    elif status == 'FAILED':
                        failed_tests.add(pending_test)
                    pending_test = None
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
