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
        return "ubuntu:20.04"
    
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
                """ls -al
###ACTION_DELIMITER###
pip install tox
###ACTION_DELIMITER###
apt-get install -y python3-pip
###ACTION_DELIMITER###
pip3 install tox
###ACTION_DELIMITER###
tox -l
###ACTION_DELIMITER###
pip3 install py
###ACTION_DELIMITER###
tox -l
###ACTION_DELIMITER###
pip3 install tox-wheel
###ACTION_DELIMITER###
ls .tox/.tox/bin/python*
###ACTION_DELIMITER###
.tox/.tox/bin/python -m pip install py
###ACTION_DELIMITER###
tox -l
###ACTION_DELIMITER###
pip3 uninstall -y tox && pip3 install tox==3.24.5
###ACTION_DELIMITER###
tox -l
###ACTION_DELIMITER###
echo 'tox -e alldeps-nocov' > /home/twisted/test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
tox -e alldeps-nocov

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
tox -e alldeps-nocov

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
tox -e alldeps-nocov

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
FROM ubuntu:20.04

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
RUN git clone https://github.com/twisted/twisted.git /home/twisted

WORKDIR /home/twisted
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("twisted", "twisted_twisted-22_8_0")
class TWISTED_TWISTED_22_8_0(Instance):
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
        passed_tests = set()
        failed_tests = set()
        skipped_tests = set()
        import re
        import json
        # --- Begin parsing logic ---
        # Passed tests: lines like 'test_name ... [OK]'
        passed_pattern = re.compile(r"^\s*(\S.*?)\s+\.\.\.\s+\[OK\]\s*$")
        # For block-based parsing
        lines = log.splitlines()
        n = len(lines)
        i = 0
        while i < n:
            line = lines[i]
            # Passed test
            m = passed_pattern.match(line)
            if m:
                passed_tests.add(m.group(1).strip())
                i += 1
                continue
            # Skipped block
            if line.strip().startswith("====") and i+1 < n and lines[i+1].strip() == "[SKIPPED]":
                # Find test names after the reason (skip reason may be 0 or more lines)
                i += 2
                # Skip reason lines (until empty line or test name)
                while i < n and lines[i].strip() != "":
                    i += 1
                # Now, collect test names until next '====' or status marker
                i += 1
                while i < n and not lines[i].strip().startswith("====") and not lines[i].strip().startswith("[") and lines[i].strip():
                    skipped_tests.add(lines[i].strip())
                    i += 1
                continue
            # Failed/Error block
            if line.strip().startswith("====") and i+1 < n and (lines[i+1].strip() == "[FAIL]" or lines[i+1].strip() == "[ERROR]"):
                # The test name is the previous non-empty line
                j = i - 1
                while j >= 0 and lines[j].strip() == "":
                    j -= 1
                if j >= 0:
                    failed_tests.add(lines[j].strip())
                i += 2
                continue
            i += 1
        # Remove overlap: failed > skipped > passed
        skipped_tests -= failed_tests
        passed_tests -= (failed_tests | skipped_tests)
        # --- End parsing logic ---
        # TODO: Implement the parse_log function
        # Implement the log parsing logic here
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
