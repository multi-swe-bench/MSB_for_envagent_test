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
        return "tiangolo/uvicorn-gunicorn-fastapi:python3.7"
    
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
echo 'pytest --no-header -rA --tb=no -p no:cacheprovider tests/' > test_commands.sh
###ACTION_DELIMITER###
pip install 'argilla[server]'
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
apt-get install -y openjdk-11-jdk
###ACTION_DELIMITER###
apt-cache search openjdk
###ACTION_DELIMITER###
apt-get install -y openjdk-17-jdk
###ACTION_DELIMITER###
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-oss-7.10.2-linux-x86_64.tar.gz
###ACTION_DELIMITER###
tar -xzf elasticsearch-oss-7.10.2-linux-x86_64.tar.gz
###ACTION_DELIMITER###
./elasticsearch-oss-7.10.2-linux-x86_64/bin/elasticsearch --allow-root &
###ACTION_DELIMITER###
ls -la
###ACTION_DELIMITER###
./elasticsearch-7.10.2/bin/elasticsearch --allow-root &
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pytest
###ACTION_DELIMITER###
adduser -q --disabled-password --gecos "" elasticsearch && chown -R elasticsearch:elasticsearch elasticsearch-7.10.2 && su elasticsearch -c "./elasticsearch-7.10.2/bin/elasticsearch &" && sleep 30
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install -e .[server]
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pytest-asyncio && pip install -e .[listeners]
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install -e .[server,listeners]
###ACTION_DELIMITER###
pip install datasets && bash test_commands.sh -v
###ACTION_DELIMITER###
python -m argilla & sleep 10 && export ARGILLA_API_URL=http://localhost:6900 && bash test_commands.sh
###ACTION_DELIMITER###
echo 'export ARGILLA_API_URL=http://localhost:6900
pytest --no-header -rA --tb=no -p no:cacheprovider tests/' > test_commands.sh && python -m argilla & sleep 20 && bash test_commands.sh
###ACTION_DELIMITER###
echo 'export ARGILLA_API_URL=http://localhost:6900
export ARGILLA_USERNAME=argilla
export ARGILLA_PASSWORD=1234
pytest --no-header -rA --tb=no -p no:cacheprovider tests/' > test_commands.sh && (python -m argilla &) && sleep 20 && until curl --output /dev/null --silent --head --fail http://localhost:6900; do sleep 5; done && bash test_commands.sh
###ACTION_DELIMITER###
fuser -k 6900/tcp; sleep 5; (python -m argilla &); sleep 15; export ARGILLA_API_URL=http://localhost:6900 ARGILLA_USERNAME=argilla ARGILLA_PASSWORD=1234; pytest -v tests/
###ACTION_DELIMITER###
pip install spacy cleanlab && ss -lptn 'sport = :6900' | awk '{print $7}' | cut -d',' -f2 | cut -d'=' -f2 | xargs -r kill -9 && sleep 5 && (python -m argilla &) && sleep 15 && export ARGILLA_API_URL=http://localhost:6900 ARGILLA_USERNAME=argilla ARGILLA_PASSWORD=1234 && pytest -v tests/
###ACTION_DELIMITER###
pip install spacy==3.4.4 cleanlab==1.0.1 && (pkill -f 'python -m argilla' || true) && sleep 5 && (python -m argilla &) && sleep 15 && export ARGILLA_API_URL=http://localhost:6900 ARGILLA_USERNAME=argilla ARGILLA_PASSWORD=1234 && pytest -v tests/
###ACTION_DELIMITER###
pip install -r requirements.txt && (pkill -f 'python -m argilla' || true) && sleep 5 && (python -m argilla &) && sleep 20 && export ARGILLA_API_URL=http://localhost:6900 ARGILLA_USERNAME=argilla ARGILLA_PASSWORD=1234 && pytest -v tests/
###ACTION_DELIMITER###
pip install spacy cleanlab && (pkill -f 'python -m argilla' || true) && sleep 5 && (python -m argilla &) && sleep 15 && export ARGILLA_API_URL=http://localhost:6900 ARGILLA_USERNAME=argilla ARGILLA_PASSWORD=1234 && pytest -v tests/
###ACTION_DELIMITER###
pip install -e .[server,listeners] && (pkill -f 'python -m argilla' || true) && sleep 5 && (python -m argilla &) && sleep 20 && export ARGILLA_API_URL=http://localhost:6900 ARGILLA_USERNAME=argilla ARGILLA_PASSWORD=1234 && pytest -v tests/
###ACTION_DELIMITER###
"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
export ARGILLA_API_URL=http://localhost:6900
export ARGILLA_USERNAME=argilla
export ARGILLA_PASSWORD=1234
pytest --no-header -rA --tb=no -p no:cacheprovider tests/

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
export ARGILLA_API_URL=http://localhost:6900
export ARGILLA_USERNAME=argilla
export ARGILLA_PASSWORD=1234
pytest --no-header -rA --tb=no -p no:cacheprovider tests/

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
export ARGILLA_API_URL=http://localhost:6900
export ARGILLA_USERNAME=argilla
export ARGILLA_PASSWORD=1234
pytest --no-header -rA --tb=no -p no:cacheprovider tests/

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
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

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


@Instance.register("argilla-io", "argilla_v1_0_1")
class ARGILLA_V1_0_1(Instance):
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
        import json
        # Split log into lines
        lines = log.split('\n')
        current_test = None
        # Regex patterns to match test status lines
        test_status_pattern = re.compile(r'^(tests/.+?)\s+(PASSED|FAILED|SKIPPED)\s+\[.+\]$')
        status_only_pattern = re.compile(r'^(PASSED|FAILED|SKIPPED)\s+\[.+\]$')
        for line in lines:
            line = line.strip()
            # Check if line contains both test name and status
            match = test_status_pattern.match(line)
            if match:
                test_name = match.group(1)
                status = match.group(2)
                if status == 'PASSED':
                    passed_tests.add(test_name)
                elif status == 'FAILED':
                    failed_tests.add(test_name)
                elif status == 'SKIPPED':
                    skipped_tests.add(test_name)
                current_test = None  # Reset current test after processing
                continue
            # Check if line is a test name (starts with 'tests/')
            if line.startswith('tests/'):
                current_test = line
                continue
            # Check if line is a status-only line (no test name)
            status_match = status_only_pattern.match(line)
            if status_match and current_test is not None:
                status = status_match.group(1)
                test_name = current_test
                if status == 'PASSED':
                    passed_tests.add(test_name)
                elif status == 'FAILED':
                    failed_tests.add(test_name)
                elif status == 'SKIPPED':
                    skipped_tests.add(test_name)
                current_test = None  # Reset current test after processing
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
