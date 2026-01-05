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
        return "python:3.9-slim"
    
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
                """ls
###ACTION_DELIMITER###
apt-get update && apt-get install -y texlive-latex-base latexmk python3-tk
###ACTION_DELIMITER###
pip install -r requirements.txt
###ACTION_DELIMITER###
echo 'pytest -v -rA .' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pytest
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install numpy==1.16.6 pytest-asyncio
###ACTION_DELIMITER###
apt-get update && apt-get install -y build-essential
###ACTION_DELIMITER###
pip install numpy==1.23.5 pytest-asyncio
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install ply
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pyquil quimb
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip uninstall -y pyquil && pip install pyquil==3.0.0
###ACTION_DELIMITER###
pip uninstall -y pyquil && pip install pyquil==2.20.0
###ACTION_DELIMITER###
pip install --force-reinstall pyquil==2.20.0
###ACTION_DELIMITER###
python -c 'from pyquil.parser import parse'
###ACTION_DELIMITER###
pip uninstall -y numpy && pip install numpy==1.26.4
###ACTION_DELIMITER###
python -c 'from pyquil.parser import parse'
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip uninstall -y numpy && pip install numpy==1.23.5
###ACTION_DELIMITER###
pip install quil==0.16.0
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install opt_einsum
###ACTION_DELIMITER###
bash test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
pytest -v -rA .

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
pytest -v -rA .

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
pytest -v -rA .

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
FROM python:3.9-slim

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


@Instance.register("quantumlib", "Cirq_3364_to_unknown")
class CIRQ_3364_TO_UNKNOWN(Instance):
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
        passed_tests: set[str] = set()  # Tests that passed successfully
        failed_tests: set[str] = set()  # Tests that failed
        skipped_tests: set[str] = set()  # Tests that were skipped
        import re
        import json
        # Parse log content to extract test names and statuses
        # Regex patterns to match test cases with status
        # Pattern 1: Test name followed by status (e.g., "cirq/...::test PASSED")
        pattern1 = re.compile(r'.*(cirq/[\w/.]+::[\w\[\]_\-]+)\s+(PASSED|FAILED|ERROR|SKIPPED|XFAIL).*')
        # Pattern 2: Status followed by test name (e.g., "FAILED cirq/...::test - error")
        pattern2 = re.compile(r'.*(PASSED|FAILED|ERROR|SKIPPED|XFAIL)\s+(cirq/[\w/.]+::[\w\[\]_\-]+).*')
        for line in log.split('\n'):
            # Check pattern 1
            match = pattern1.search(line)
            if match:
                test_name = match.group(1)
                status = match.group(2)
            else:
                # Check pattern 2
                match = pattern2.search(line)
                if match:
                    status = match.group(1)
                    test_name = match.group(2)
                else:
                    continue  # No match
            # Categorize the test based on status
            if status == 'PASSED':
                passed_tests.add(test_name)
            elif status in ('FAILED', 'ERROR'):
                failed_tests.add(test_name)
            elif status in ('SKIPPED', 'XFAIL'):
                skipped_tests.add(test_name)
            # Add handling for other statuses if present in logs
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
