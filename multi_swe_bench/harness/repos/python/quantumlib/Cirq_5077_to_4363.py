import re

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
apt-get update && xargs apt-get install -y < apt-system-requirements.txt
###ACTION_DELIMITER###
pip install -e ".[dev_env]"
###ACTION_DELIMITER###
apt-get install -y python3-pip
###ACTION_DELIMITER###
pip install -e ".[dev_env]"
###ACTION_DELIMITER###
python3 -m venv venv
###ACTION_DELIMITER###
apt-get install -y python3.12-venv
###ACTION_DELIMITER###
python3 -m venv venv
###ACTION_DELIMITER###
source venv/bin/activate
###ACTION_DELIMITER###
pip install -e ".[dev_env]"
###ACTION_DELIMITER###
sed -i 's/from setuptools import setup/from setuptools import setup, find_packages/' setup.py && sed -i 's/setup(/setup(packages=find_packages(exclude=["check", "rtd_docs", "dev_tools"]), /' setup.py
###ACTION_DELIMITER###
pip install -e ".[dev_env]"
###ACTION_DELIMITER###
pip install -e ./cirq-core -e ./cirq-aqt -e ./cirq-google -e ./cirq-ionq -e ./cirq-pasqal -e ./cirq-rigetti -e ./cirq-web
###ACTION_DELIMITER###
echo './venv/bin/pytest -v --no-header -rA --tb=no -p no:cacheprovider ./...' > test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
echo './venv/bin/pytest -v --no-header -rA --tb=no -p no:cacheprovider cirq-core/tests cirq-aqt/tests cirq-google/tests cirq-ionq/tests cirq-pasqal/tests cirq-rigetti/tests cirq-web/tests examples/ dev_tools/tests' > test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pytest
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
ls cirq-core
###ACTION_DELIMITER###
ls cirq-core/cirq
###ACTION_DELIMITER###
find . -name 'test_*.py'
###ACTION_DELIMITER###
ls check
###ACTION_DELIMITER###
cat check/pytest
###ACTION_DELIMITER###
echo './check/pytest' > test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install setuptools filelock
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install ply
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install quimb
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install freezegun astroid
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pylint
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pylint==2.17.0
###ACTION_DELIMITER###
pip install pylint==2.12.0
###ACTION_DELIMITER###
echo './check/pytest --ignore=dev_tools/pylint_copyright_checker_test.py' > test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
./check/pytest --ignore=dev_tools/pylint_copyright_checker_test.py

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
./check/pytest --ignore=dev_tools/pylint_copyright_checker_test.py

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
./check/pytest --ignore=dev_tools/pylint_copyright_checker_test.py

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
RUN git clone https://github.com/quantumlib/Cirq.git /home/Cirq

WORKDIR /home/Cirq
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("quantumlib", "Cirq_5077_to_4363")
class CIRQ_5077_TO_4363(Instance):
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
        passed_tests = set()
        failed_tests = set()
        skipped_tests = set()
        # Extract FAILED/ERROR tests (explicit lines)
        failed_pattern = re.compile(r'(FAILED|ERROR)\s+([\w\/\-\.]+::[\w\[\]\/\-]+)', re.MULTILINE)
        failed_tests.update(match[1] for match in failed_pattern.findall(log))
        # Extract test session lines (e.g., "cirq-aqt/..._test.py .sF...")
        session_pattern = re.compile(r'([\w\/\-\.]+\.py)\s+([\.\sFEs]+)', re.MULTILINE)
        for file, status_chars in session_pattern.findall(log):
            # Split status characters (ignore whitespace)
            statuses = [c for c in status_chars if c != ' ']
            for idx, status in enumerate(statuses, 1):
                test_name = f"{file}::test_{idx}"  # Infer test name from index
                if status == '.':
                    passed_tests.add(test_name)
                elif status == 's':
                    skipped_tests.add(test_name)
                elif status in 'FE':
                    failed_tests.add(test_name)
        # Extract explicit SKIPPED tests (e.g., "SKIPPED: ...")
        skipped_pattern = re.compile(r'SKIPPED\s*:\s*([\w\/\-\.]+::[\w\[\]\/\-]+)', re.MULTILINE | re.IGNORECASE)
        skipped_tests.update(skipped_pattern.findall(log))
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
