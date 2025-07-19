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
python -m pip install pytest-cov pytest-json-report
###ACTION_DELIMITER###
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
python -m pip install traitlets
###ACTION_DELIMITER###
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
python -m pip install stack_data
###ACTION_DELIMITER###
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
python -m pip install pexpect
###ACTION_DELIMITER###
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
python -m pip install pickleshare
###ACTION_DELIMITER###
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
python -m pip install backcall
###ACTION_DELIMITER###
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
python -m pip install decorator
###ACTION_DELIMITER###
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
python -m pip install prompt-toolkit
###ACTION_DELIMITER###
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
python -m pip install testpath
###ACTION_DELIMITER###
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
python -m pip install pytest==6.2.5
###ACTION_DELIMITER###
python -m pip install --upgrade -e .[test_extra]
###ACTION_DELIMITER###
python -m pip install pytest-cov pytest-json-report pytest-metadata>=3.1.1 && pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
python -m pip install pytest==6.2.5 pytest-metadata==2.0.0 && pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
python -m pip install pytest==7.1.1 pytest-metadata==2.0.0 && pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-
###ACTION_DELIMITER###
echo 'pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-' > test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-

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
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-

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
pytest --color=yes -raXxs --cov --cov-report=xml --json-report --json-report-file=-

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
RUN git clone https://github.com/ipython/ipython.git /home/ipython

WORKDIR /home/ipython
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("ipython", "ipython_8_14_0")
class IPYTHON_8_14_0(Instance):
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
        passed_tests = set[str]()  # Tests that passed successfully
        failed_tests = set[str]()  # Tests that failed
        skipped_tests = set[str]()  # Tests that were skipped
        import re
        # Extract failed tests
        failed_matches = re.findall(r"FAILED (\S+)", log)
        failed_tests.update(failed_matches)
        # Extract skipped tests
        skipped_matches = re.findall(r"SKIPPED \[\d+\] (\S+):", log)
        skipped_tests.update(skipped_matches)
        # Extract all test names from the log
        all_test_matches = re.findall(r"(\S+\.py::\S+|\S+\.py:\d+)", log)
        all_tests = set(all_test_matches)
        # Calculate passed tests
        passed_tests = all_tests - failed_tests - skipped_tests
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
