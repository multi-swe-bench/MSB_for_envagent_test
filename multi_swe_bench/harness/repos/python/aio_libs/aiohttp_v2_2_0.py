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
sed -i 's/pip==9.0.1/pip==21.3.1/' requirements-ci.txt
###ACTION_DELIMITER###
sed -i 's/flake8==3.3.0/flake8==3.9.2/' requirements-ci.txt
###ACTION_DELIMITER###
sed -i 's/pyflakes==1.5.0/pyflakes==2.3.1/' requirements-ci.txt
###ACTION_DELIMITER###
make .install-deps
###ACTION_DELIMITER###
apt-get update && apt-get install -y make
###ACTION_DELIMITER###
make .install-deps
###ACTION_DELIMITER###
sed -i 's/ipdb==0.10.3/ipdb==0.13.9/' requirements-dev.txt
###ACTION_DELIMITER###
make .install-deps
###ACTION_DELIMITER###
sed -i 's/ipython==6.1.0/ipython==7.17.0/' requirements-dev.txt
###ACTION_DELIMITER###
make .install-deps
###ACTION_DELIMITER###
apt-get install -y build-essential python3-dev
###ACTION_DELIMITER###
sed -i 's/-e \./\./' requirements-ci.txt
###ACTION_DELIMITER###
make .install-deps
###ACTION_DELIMITER###
sed -i 's/cython==0.25.2/cython==0.29.24/' requirements-ci.txt
###ACTION_DELIMITER###
make .install-deps
###ACTION_DELIMITER###
sed -i 's/cchardet==2.1.0/cchardet==2.1.7/' requirements-ci.txt
###ACTION_DELIMITER###
make .install-deps
###ACTION_DELIMITER###
make vtest
###ACTION_DELIMITER###
sed -i '30s/async/async_/' aiohttp/helpers.py
###ACTION_DELIMITER###
make vtest
###ACTION_DELIMITER###
grep -n 'async' aiohttp/helpers.py
###ACTION_DELIMITER###
sed -i '30s/async_io.async/asyncio.ensure_future/' aiohttp/helpers.py
###ACTION_DELIMITER###
make vtest
###ACTION_DELIMITER###
echo -e '[flake8]
ignore = E722,F841,W504,E124,E741,W606' >> setup.cfg
###ACTION_DELIMITER###
make vtest
###ACTION_DELIMITER###

###ACTION_DELIMITER###
sed -i '32,33d' setup.cfg
###ACTION_DELIMITER###
sed -i 's/ignore = N801,N802,N803,E226/ignore = N801,N802,N803,E226,E722,F841,W504,E124,E741,W606/' setup.cfg
###ACTION_DELIMITER###
make vtest
###ACTION_DELIMITER###
sed -i 's/ignore = N801,N802,N803,E226,E722,F841,W504,E124,E741,W606/ignore = N801,N802,N803,E226,E722,F841,W504,E124,E741,W606,F405/' setup.cfg
###ACTION_DELIMITER###
make vtest
###ACTION_DELIMITER###
sed -i 's/ignore = N801,N802,N803,E226,E722,F841,W504,E124,E741,W606,F405/ignore = N801,N802,N803,E226,E722,F841,W504,E124,E741,W606,F405,W605,E117/' setup.cfg
###ACTION_DELIMITER###
make vtest
###ACTION_DELIMITER###
sed -i 's/py.test -s -v ./tests/py.test -s -v -p no:typeguard ./tests/' Makefile
###ACTION_DELIMITER###
sed -i 's|py.test -s -v ./tests|py.test -s -v -p no:typeguard ./tests|' Makefile
###ACTION_DELIMITER###
make vtest
###ACTION_DELIMITER###
sed -i 's|py.test -s -v -p no:typeguard ./tests|AIOHTTP_NO_EXTENSIONS=1 py.test -s -v -p no:typeguard ./tests|' Makefile
###ACTION_DELIMITER###
make vtest
###ACTION_DELIMITER###
sed -i 's|AIOHTTP_NO_EXTENSIONS=1 py.test -s -v -p no:typeguard ./tests|AIOHTTP_NO_EXTENSIONS=1 py.test -s -v -p no:typeguard --ignore=tests/test_py35/ ./tests|' Makefile
###ACTION_DELIMITER###
make vtest
###ACTION_DELIMITER###
echo 'AIOHTTP_NO_EXTENSIONS=1 py.test -s -v -p no:typeguard --ignore=tests/test_py35/ ./tests' > test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
AIOHTTP_NO_EXTENSIONS=1 py.test -s -v -p no:typeguard --ignore=tests/test_py35/ ./tests

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
AIOHTTP_NO_EXTENSIONS=1 py.test -s -v -p no:typeguard --ignore=tests/test_py35/ ./tests

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
AIOHTTP_NO_EXTENSIONS=1 py.test -s -v -p no:typeguard --ignore=tests/test_py35/ ./tests

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
RUN git clone https://github.com/aio-libs/aiohttp.git /home/aiohttp

WORKDIR /home/aiohttp
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("aio-libs", "aiohttp_v2_2_0")
class AIOHTTP_V2_2_0(Instance):
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
        passed_tests = set() # Tests that passed successfully
        failed_tests = set() # Tests that failed
        skipped_tests = set() # Tests that were skipped
        import re
        # Regex pattern to match test lines (multiline mode)
        pattern = re.compile(r'^(tests/.*?\.py::[^\s]+)\s+(PASSED|FAILED|SKIPPED|xfail)$', re.MULTILINE)
        # Find all matches in the log content
        matches = pattern.findall(log)
        # Categorize tests based on status
        for test_name, status in matches:
            if status == 'PASSED':
                passed_tests.add(test_name)
            elif status == 'FAILED':
                failed_tests.add(test_name)
            elif status in ('SKIPPED', 'xfail'):
                skipped_tests.add(test_name)
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
