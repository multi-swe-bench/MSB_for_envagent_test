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
                """ls -l /home/Cirq
###ACTION_DELIMITER###
cat apt-system-requirements.txt
###ACTION_DELIMITER###
apt-get update && apt-get install -y texlive-latex-base latexmk python3-tk
###ACTION_DELIMITER###
cat setup.py
###ACTION_DELIMITER###
python3 --version
###ACTION_DELIMITER###
apt-get update && apt-get install -y python3.10 python3.10-dev python3.10-distutils python3.10-tk
###ACTION_DELIMITER###
echo 'deb http://deb.debian.org/debian bookworm-backports main' > /etc/apt/sources.list.d/backports.list && apt-get update && apt-get install -y -t bookworm-backports python3.10 python3.10-dev python3.10-distutils python3.10-tk
###ACTION_DELIMITER###
apt-cache search python3.10
###ACTION_DELIMITER###
apt-get update && apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl && wget https://www.python.org/ftp/python/3.10.13/Python-3.10.13.tgz && tar xzf Python-3.10.13.tgz && cd Python-3.10.13 && ./configure --enable-optimizations && make -j 4 && make install
###ACTION_DELIMITER###
python3 --version
###ACTION_DELIMITER###
cd /home/Cirq && pip install -e .
###ACTION_DELIMITER###
pip install --upgrade pip
###ACTION_DELIMITER###
pip install --upgrade setuptools wheel
###ACTION_DELIMITER###
grep -r 'install' /home/Cirq/*/setup.py
###ACTION_DELIMITER###
rm -rf /home/Cirq/Python-3.10.13
###ACTION_DELIMITER###
pip install -e .
###ACTION_DELIMITER###
pip install -e ./cirq-core -e ./cirq-aqt -e ./cirq-google -e ./cirq-ionq -e ./cirq-pasqal -e ./cirq-rigetti -e ./cirq-web
###ACTION_DELIMITER###
echo 'pytest -v -rA --tb=no -p no:cacheprovider ./...' > /home/Cirq/test_commands.sh
###ACTION_DELIMITER###
cat /home/Cirq/test_commands.sh
###ACTION_DELIMITER###
bash /home/Cirq/test_commands.sh
###ACTION_DELIMITER###
pip install pytest
###ACTION_DELIMITER###
bash /home/Cirq/test_commands.sh
###ACTION_DELIMITER###
echo 'pytest -v -rA --tb=no -p no:cacheprovider .' > /home/Cirq/test_commands.sh && bash /home/Cirq/test_commands.sh
###ACTION_DELIMITER###
pip install filelock pytest-asyncio && bash /home/Cirq/test_commands.sh
###ACTION_DELIMITER###
pip install quimb pyparsing svgwrite pylint && bash /home/Cirq/test_commands.sh
###ACTION_DELIMITER###
pip install lark-parser cairosvg google-cloud-bigquery grpcio-tools && bash /home/Cirq/test_commands.sh
###ACTION_DELIMITER###
apt-get update && apt-get install -y libcairo2-dev && pip install -e .[dev_env] && bash /home/Cirq/test_commands.sh
###ACTION_DELIMITER###
echo 'pytest -v -rA --tb=no -p no:cacheprovider . -k "not docker_test"' > /home/Cirq/test_commands.sh && bash /home/Cirq/test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
pytest -v -rA --tb=no -p no:cacheprovider . -k "not docker_test"

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
pytest -v -rA --tb=no -p no:cacheprovider . -k "not docker_test"

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
pytest -v -rA --tb=no -p no:cacheprovider . -k "not docker_test"

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

# Choose an appropriate base image based on the project's requirements - replace python:3.9-slim with actual base image
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


@Instance.register("quantumlib", "Cirq_7018_to_6516")
class CIRQ_7018_TO_6516(Instance):
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
        passed_tests = set[str]()
        failed_tests = set[str]()
        skipped_tests = set[str]()
        import re
        import json
        pattern = re.compile(
            r'^(?:\[\s*\d+\s*\] )?(.*?\.py::[^\s]+)\s+(PASSED|FAILED|SKIPPED|XFAIL|XPASS)\b.*|'
            r'^(?:\[\s*\d+\s*\] )?(PASSED|FAILED|SKIPPED|XFAIL|XPASS)\s+(.*?\.py::[^\s]+)\b.*'
        )
        for line in log.split('\n'):
            line = line.strip()
            match = pattern.match(line)
            if match:
                # Extract test name and status
                if match.group(1) and match.group(2):
                    test_name = match.group(1)
                    status = match.group(2)
                elif match.group(3) and match.group(4):
                    test_name = match.group(4)
                    status = match.group(3)
                else:
                    continue  # No match
                # Clean test name
                test_name = test_name.strip()
                # Add to appropriate set
                if status == 'PASSED':
                    passed_tests.add(test_name)
                elif status == 'FAILED':
                    failed_tests.add(test_name)
                elif status == 'SKIPPED':
                    skipped_tests.add(test_name)
                elif status == 'XFAIL':
                    failed_tests.add(test_name)
                elif status == 'XPASS':
                    passed_tests.add(test_name)
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
