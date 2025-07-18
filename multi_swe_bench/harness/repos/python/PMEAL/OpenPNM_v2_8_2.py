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
ls requirements
###ACTION_DELIMITER###
pip install -r requirements/test_requirements.txt
###ACTION_DELIMITER###
echo 'pytest -v' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install py
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install -e .
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install chemicals==1.2.0
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install chemicals==1.3.2
###ACTION_DELIMITER###
pip install chemicals==1.3.0
###ACTION_DELIMITER###
pip install chemicals==1.1.0
###ACTION_DELIMITER###
pip install chemicals==1.1.1
###ACTION_DELIMITER###
pip install chemicals==1.0.0
###ACTION_DELIMITER###
pip install chemicals==0.1.5
###ACTION_DELIMITER###
echo 'pytest tests/unit -v' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install numpy==1.26.4
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install numpy==1.21.6
###ACTION_DELIMITER###
pip install chemicals==1.2.0 numpy==1.26.4
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install chemicals==0.1.5
###ACTION_DELIMITER###
pip install chemicals==0.1.5 numpy==1.23.5
###ACTION_DELIMITER###
bash test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest tests/unit -v

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
pytest tests/unit -v

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
pytest tests/unit -v

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
RUN git clone https://github.com/PMEAL/OpenPNM.git /home/OpenPNM

WORKDIR /home/OpenPNM
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("PMEAL", "OpenPNM_v2_8_2")
class OPENPNM_V2_8_2(Instance):
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
        # Pattern for passed tests: "test_name PASSED"
        pattern_passed = re.compile(r'^(.*?)\s+PASSED$', re.MULTILINE)
        passed_matches = pattern_passed.findall(log)
        passed_tests.update([test.strip() for test in passed_matches])
        # Patterns for failed tests: "test_name FAILED" and "FAILED test_name ..."
        pattern_failed1 = re.compile(r'^(.*?)\s+FAILED$', re.MULTILINE)
        pattern_failed2 = re.compile(r'^FAILED\s+(.*?)(\s+-.*)?$', re.MULTILINE)
        failed_matches1 = pattern_failed1.findall(log)
        failed_matches2 = pattern_failed2.findall(log)
        failed_matches = failed_matches1 + [match[0] for match in failed_matches2]
        failed_tests.update([test.strip() for test in failed_matches])
        # Patterns for skipped tests: "test_name SKIPPED" and "SKIPPED test_name ..."
        pattern_skipped1 = re.compile(r'^(.*?)\s+SKIPPED$', re.MULTILINE)
        pattern_skipped2 = re.compile(r'^SKIPPED\s+(.*?)(\s+-.*)?$', re.MULTILINE)
        skipped_matches1 = pattern_skipped1.findall(log)
        skipped_matches2 = pattern_skipped2.findall(log)
        skipped_matches = skipped_matches1 + [match[0] for match in skipped_matches2]
        skipped_tests.update([test.strip() for test in skipped_matches])
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
