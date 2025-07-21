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
        return "python:3.9-slim"
    
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
                """ls
###ACTION_DELIMITER###
pip install spacy==3.5.0 && pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.5.0/en_core_web_sm-3.5.0.tar.gz
###ACTION_DELIMITER###
echo 'pytest -v --cov=argilla --cov-report=xml' > /home/argilla/test_commands.sh
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pip install pytest
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pip install -e ".[server,listeners]"
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pip install factory_boy~=3.2.1
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pip install pytest-cov
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pip install cleanlab~=2.0.0 pytest-asyncio
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
wget https://artifacts.opensearch.org/releases/bundle/opensearch/2.11.0/opensearch-2.11.0-linux-x64.tar.gz && tar -xzf opensearch-2.11.0-linux-x64.tar.gz && cd opensearch-2.11.0 && sed -i 's/-Xms1g/-Xms512m/' config/jvm.options && sed -i 's/-Xmx1g/-Xmx512m/' config/jvm.options && echo 'plugins.security.disabled: true' >> config/opensearch.yml && ./bin/opensearch -d
###ACTION_DELIMITER###
apt-get update && apt-get install -y wget
###ACTION_DELIMITER###
wget https://artifacts.opensearch.org/releases/bundle/opensearch/2.11.0/opensearch-2.11.0-linux-x64.tar.gz && tar -xzf opensearch-2.11.0-linux-x64.tar.gz && cd opensearch-2.11.0 && sed -i 's/-Xms1g/-Xms512m/' config/jvm.options && sed -i 's/-Xmx1g/-Xmx512m/' config/jvm.options && echo 'plugins.security.disabled: true' >> config/opensearch.yml && ./bin/opensearch -d
###ACTION_DELIMITER###
apt-get update && apt-get install -y procps
###ACTION_DELIMITER###
adduser --disabled-password --gecos "" opensearch && chown -R opensearch:opensearch /home/argilla/opensearch-2.11.0 && su - opensearch -c "/home/argilla/opensearch-2.11.0/bin/opensearch -d"
###ACTION_DELIMITER###
ps aux | grep opensearch
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
ls tests
###ACTION_DELIMITER###
cd /home/argilla
###ACTION_DELIMITER###
ls tests
###ACTION_DELIMITER###
echo 'pytest tests -v --cov=argilla --cov-report=xml' > /home/argilla/test_commands.sh
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pip install 'datasets>1.17.0,!=2.3.2'
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
alembic upgrade head
###ACTION_DELIMITER###
alembic --config src/argilla/alembic.ini upgrade head
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pip install flair==0.10 faiss-cpu flyingsquid pgmpy plotly>=4.1.0 snorkel>=0.9.7 'transformers[torch]>=4.19.0' evaluate seqeval setfit span_marker openai rich==13.0.1
###ACTION_DELIMITER###
pip install 'numpy<1.24.0'
###ACTION_DELIMITER###
pip install faiss-cpu==1.7.4
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pytest tests/client/apis/test_base.py::test_api_compatibility -v -s
###ACTION_DELIMITER###
pip install pytest-mock
###ACTION_DELIMITER###
pytest tests/client/apis/test_base.py::test_api_compatibility -v -s
###ACTION_DELIMITER###
pip install flair==0.10 'transformers[torch]>=4.19.0' openai seqeval setfit span_marker evaluate snorkel>=0.9.7 pgmpy plotly>=4.1.0 flyingsquid
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest tests -v --cov=argilla --cov-report=xml

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
pytest tests -v --cov=argilla --cov-report=xml

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
pytest tests -v --cov=argilla --cov-report=xml

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
RUN git clone https://github.com/argilla-io/argilla.git /home/argilla

WORKDIR /home/argilla
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("argilla-io", "argilla_v1_7_0")
class ARGILLA_V1_7_0(Instance):
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
        # Define regex patterns
        test_status_pattern = re.compile(r'^(.+?\.py::.+?) (PASSED|FAILED|SKIPPED) \[.+\]$')
        test_name_pattern = re.compile(r'^(.+?\.py::.+?)\s*$')
        status_pattern = re.compile(r'^(PASSED|FAILED|SKIPPED)\s+\[.+\]$')
        current_test = None
        # Iterate through each line in the log
        for line in log.split('\n'):
            # Check for lines with both test name and status
            status_match = test_status_pattern.match(line)
            if status_match:
                test_name = status_match.group(1)
                status = status_match.group(2)
                if status == 'PASSED':
                    passed_tests.add(test_name)
                elif status == 'FAILED':
                    failed_tests.add(test_name)
                elif status == 'SKIPPED':
                    skipped_tests.add(test_name)
                continue
            # Check for test name lines (without status)
            name_match = test_name_pattern.match(line)
            if name_match:
                current_test = name_match.group(1)
                continue
            # Check for status lines (without test name)
            status_only_match = status_pattern.match(line)
            if status_only_match:
                if current_test:
                    status = status_only_match.group(1)
                    if status == 'PASSED':
                        passed_tests.add(current_test)
                    elif status == 'FAILED':
                        failed_tests.add(current_test)
                    elif status == 'SKIPPED':
                        skipped_tests.add(current_test)
                    current_test = None  # Reset after processing
                continue
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
