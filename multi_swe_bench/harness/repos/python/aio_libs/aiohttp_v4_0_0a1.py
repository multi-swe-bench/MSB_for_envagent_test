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
echo 'pytest -v -rA --tb=no -p no:cacheprovider' > test_commands.sh
###ACTION_DELIMITER###
apt-get update && apt-get install -y build-essential libhttp-parser-dev
###ACTION_DELIMITER###
pip install -r requirements/ci.txt
###ACTION_DELIMITER###
git submodule update --init
###ACTION_DELIMITER###
sed -i 's/git:\/\/github.com/https:\/\/github.com/g' .gitmodules
###ACTION_DELIMITER###
git submodule update --init
###ACTION_DELIMITER###
cat .gitmodules
###ACTION_DELIMITER###

###ACTION_DELIMITER###
sed -i '/vendor\/http-parser\/http_parser.c/d' setup.py && sed -i '/define_macros/a \          extra_link_args=["-lhttp_parser"],' setup.py
###ACTION_DELIMITER###
pip install -r requirements/ci.txt
###ACTION_DELIMITER###
mkdir -p vendor/http-parser && touch vendor/http-parser/http_parser.h
###ACTION_DELIMITER###
sed -i '21,26 s/^/#/' setup.py
###ACTION_DELIMITER###
pip install -r requirements/ci.txt
###ACTION_DELIMITER###
sed -i 's/codecov==2.0.15/codecov==2.1.13/' requirements/ci.txt
###ACTION_DELIMITER###
pip install -r requirements/ci.txt
###ACTION_DELIMITER###
cat requirements/ci.txt
###ACTION_DELIMITER###
cat requirements/ci-wheel.txt
###ACTION_DELIMITER###
sed -i 's/codecov==2.0.15/codecov==2.1.13/' requirements/ci-wheel.txt
###ACTION_DELIMITER###
pip install -r requirements/ci.txt
###ACTION_DELIMITER###
pip install cython
###ACTION_DELIMITER###
python setup.py build_ext --inplace
###ACTION_DELIMITER###
cython aiohttp/_websocket.pyx
###ACTION_DELIMITER###
python setup.py build_ext --inplace
###ACTION_DELIMITER###
cython aiohttp/_http_parser.pyx
###ACTION_DELIMITER###
python setup.py build_ext --inplace
###ACTION_DELIMITER###
find /usr -name http_parser.h
###ACTION_DELIMITER###
sed -i 's|#include "vendor/http-parser/http_parser.h"|#include <http_parser.h>|g' aiohttp/_http_parser.c
###ACTION_DELIMITER###
mkdir -p vendor/http-parser && wget https://raw.githubusercontent.com/nodejs/http-parser/54f55a2/http_parser.h -O vendor/http-parser/http_parser.h
###ACTION_DELIMITER###
apt-get update && apt-get install -y wget
###ACTION_DELIMITER###
mkdir -p vendor/http-parser && wget https://raw.githubusercontent.com/nodejs/http-parser/54f55a2/http_parser.h -O vendor/http-parser/http_parser.h
###ACTION_DELIMITER###
python setup.py build_ext --inplace
###ACTION_DELIMITER###
cython aiohttp/_frozenlist.pyx
###ACTION_DELIMITER###
python setup.py build_ext --inplace
###ACTION_DELIMITER###
cython aiohttp/_helpers.pyx
###ACTION_DELIMITER###
ls aiohttp/_helpers.c
###ACTION_DELIMITER###
python setup.py build_ext --inplace
###ACTION_DELIMITER###
cython aiohttp/_http_writer.pyx
###ACTION_DELIMITER###
python setup.py build_ext --inplace
###ACTION_DELIMITER###
pip install -r requirements/ci.txt
###ACTION_DELIMITER###
echo 'pytest -v -rA --tb=no -p no:cacheprovider' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest -v -rA --tb=no -p no:cacheprovider

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
pytest -v -rA --tb=no -p no:cacheprovider

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
pytest -v -rA --tb=no -p no:cacheprovider

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
RUN git clone https://github.com/aio-libs/aiohttp.git /home/aiohttp

WORKDIR /home/aiohttp
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("aio-libs", "aiohttp_v4_0_0a1")
class AIOHTTP_V4_0_0A1(Instance):
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
        # Use regex to find test cases and their statuses
        pattern = re.compile(r'^(.*?)\s+(PASSED|FAILED|SKIPPED)\s+\[\s*\d+%\s*\]$', re.MULTILINE)
        matches = pattern.findall(log)
        for test_name, status in matches:
            # Clean the test name (in case of extra spaces)
            test_name = test_name.strip()
            if status == 'PASSED':
                passed_tests.add(test_name)
            elif status == 'FAILED':
                failed_tests.add(test_name)
            elif status == 'SKIPPED':
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
