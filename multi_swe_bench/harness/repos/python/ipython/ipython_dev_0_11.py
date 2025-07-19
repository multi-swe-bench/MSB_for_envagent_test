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
pip install nose
###ACTION_DELIMITER###
ls -a
###ACTION_DELIMITER###
python setup.py test
###ACTION_DELIMITER###
python --version
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
apt-get install -y python2.7
###ACTION_DELIMITER###
apt-cache search python2
###ACTION_DELIMITER###
echo 'deb http://deb.debian.org/debian bullseye main' >> /etc/apt/sources.list
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
apt-get install -y python2.7
###ACTION_DELIMITER###
apt-get install -y python-pip
###ACTION_DELIMITER###
curl -O https://bootstrap.pypa.io/pip/2.7/get-pip.py
###ACTION_DELIMITER###
apt-get install -y curl
###ACTION_DELIMITER###
curl -O https://bootstrap.pypa.io/pip/2.7/get-pip.py
###ACTION_DELIMITER###
python2.7 get-pip.py
###ACTION_DELIMITER###
pip2.7 install nose
###ACTION_DELIMITER###
python2.7 setup.py test
###ACTION_DELIMITER###
nosetests -v
###ACTION_DELIMITER###
pip2.7 install matplotlib pyzmq
###ACTION_DELIMITER###
echo 'nosetests -v' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip2.7 install pyzmq==2.2.0
###ACTION_DELIMITER###
apt-get install -y build-essential
###ACTION_DELIMITER###
pip2.7 install pyzmq==2.2.0
###ACTION_DELIMITER###
apt-get install -y libzmq3-dev
###ACTION_DELIMITER###
pip2.7 install pyzmq==2.2.0
###ACTION_DELIMITER###
apt-get install -y python2.7-dev
###ACTION_DELIMITER###
apt-get install -y python-zmq
###ACTION_DELIMITER###
apt-get install -y python2-zmq
###ACTION_DELIMITER###
pip2.7 install pyzmq==14.7.0
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip2.7 install pyzmq==2.1.11
###ACTION_DELIMITER###
pip2.7 install pyzmq==2.1.5
###ACTION_DELIMITER###
pip2.7 install pyzmq==2.1.7
###ACTION_DELIMITER###
pip2.7 install pyzmq==2.1.4
###ACTION_DELIMITER###
pip2.7 install pyzmq==2.2.0
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
nosetests -v

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
nosetests -v

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
nosetests -v

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

# Choose an appropriate base image based on the project's requirements - replace python:3.10-slim with actual base image
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
RUN git clone https://github.com/ipython/ipython.git /home/ipython

WORKDIR /home/ipython
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("ipython", "ipython_dev-0_11")
class IPYTHON_DEV_0_11(Instance):
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
        # Regex pattern to match valid test lines with status (ok, SKIP, FAIL, ERROR)
        # Captures test names with alphanumerics, spaces, parentheses, and dots
        pattern = re.compile(r'^([\w\s()\.-]+)\s+\.\.\.\s+(ok|SKIP|FAIL|ERROR)\s*$', re.MULTILINE)
        for match in pattern.finditer(log):
            test_name = match.group(1).strip()
            status = match.group(2)
            if status == 'ok':
                passed_tests.add(test_name)
            elif status == 'SKIP':
                skipped_tests.add(test_name)
            elif status in ('FAIL', 'ERROR'):
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
