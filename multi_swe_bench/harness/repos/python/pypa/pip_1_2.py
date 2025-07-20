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
python --version
###ACTION_DELIMITER###
pip install --upgrade pip
###ACTION_DELIMITER###
python -m ensurepip --upgrade
###ACTION_DELIMITER###
pip install nose virtualenv>=1.7 scripttest>=1.1.1 mock
###ACTION_DELIMITER###
python -m pip install nose virtualenv>=1.7 scripttest>=1.1.1 mock
###ACTION_DELIMITER###
python -m pip list
###ACTION_DELIMITER###
python -m pip --version
###ACTION_DELIMITER###
python -m pip install -v nose virtualenv>=1.7 scripttest>=1.1.1 mock
###ACTION_DELIMITER###
python -m pip install -e ".[testing]"
###ACTION_DELIMITER###
python -m pip install --upgrade setuptools
###ACTION_DELIMITER###
python -m pip install --upgrade setuptools --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
python -m pip install -v nose virtualenv>=1.7 scripttest>=1.1.1 mock
###ACTION_DELIMITER###
python -m pip list
###ACTION_DELIMITER###
python -m pip install setuptools==44.0.0
###ACTION_DELIMITER###
python -m pip install pip==20.3.4
###ACTION_DELIMITER###
python -m ensurepip --upgrade
###ACTION_DELIMITER###
python -m venv venv && source venv/bin/activate && python -m pip install --upgrade pip && python -m pip install setuptools==44.0.0
###ACTION_DELIMITER###
python -m venv venv && source venv/bin/activate && python -m pip install --upgrade pip --index-url https://pypi.org/simple/ && python -m pip install setuptools==44.0.0 --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
python -m venv venv && source venv/bin/activate && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py && python -m pip install setuptools==44.0.0
###ACTION_DELIMITER###
apt-get update && apt-get install -y curl && python -m venv venv && source venv/bin/activate && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py && python -m pip install setuptools==44.0.0
###ACTION_DELIMITER###
source venv/bin/activate && python -m pip install setuptools==44.0.0 --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
source venv/bin/activate && python -m pip install nose virtualenv>=1.7 scripttest>=1.1.1 mock --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
source venv/bin/activate && python -m pip list
###ACTION_DELIMITER###
apt-get update && apt-get install -y python2.7 python2.7-pip && python2.7 -m pip install virtualenv && python2.7 -m virtualenv venv27 && source venv27/bin/activate && pip install nose virtualenv>=1.7 scripttest>=1.1.1 mock --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
apt-get update && apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl
###ACTION_DELIMITER###
wget https://www.python.org/ftp/python/3.4.10/Python-3.4.10.tgz && tar xzf Python-3.4.10.tgz && cd Python-3.4.10 && ./configure --enable-optimizations && make -j 4 && make install && cd .. && python3.4 -m venv venv34 && source venv34/bin/activate && pip install nose virtualenv>=1.7 scripttest>=1.1.1 mock --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
cd Python-3.4.10 && make clean && ./configure --with-ssl && make -j4 && make install && cd .. && python3.4 -m venv venv34 && source venv34/bin/activate && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py && pip install nose virtualenv>=1.7 scripttest>=1.1.1 mock --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
source venv34/bin/activate && curl https://bootstrap.pypa.io/pip/3.4/get-pip.py -o get-pip.py && python get-pip.py && pip install nose virtualenv>=1.7 scripttest>=1.1.1 mock --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
apt-get install -y libssl-dev && cd Python-3.4.10 && make clean && ./configure && make -j4 && make install && cd .. && source venv34/bin/activate && curl https://bootstrap.pypa.io/pip/3.4/get-pip.py -o get-pip.py && python get-pip.py --index-url http://pypi.python.org/simple/ --trusted-host pypi.python.org && pip install nose virtualenv>=1.7 scripttest>=1.1.1 mock --index-url http://pypi.python.org/simple/ --trusted-host pypi.python.org
###ACTION_DELIMITER###
cd Python-3.4.10 && make clean && ./configure --with-ssl && make -j4 && make install && cd .. && python3.4 -m venv venv34 && source venv34/bin/activate && curl https://bootstrap.pypa.io/pip/3.4/get-pip.py -o get-pip.py && python get-pip.py --index-url http://pypi.python.org/simple/ --trusted-host pypi.python.org && pip install nose virtualenv>=1.7 scripttest>=1.1.1 mock --index-url http://pypi.python.org/simple/ --trusted-host pypi.python.org
###ACTION_DELIMITER###
apt-get update && apt-get install -y libssl-dev zlib1g-dev && wget https://www.python.org/ftp/python/2.7.18/Python-2.7.18.tgz && tar xzf Python-2.7.18.tgz && cd Python-2.7.18 && ./configure --with-ssl && make -j4 && make install && cd .. && python2.7 -m pip install --upgrade pip==19.1.1 && pip2.7 install nose virtualenv>=1.7 scripttest>=1.1.1 mock --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
wget https://bootstrap.pypa.io/ez_setup.py -O - | python2.7 && python2.7 -m easy_install pip==19.1.1 && pip2.7 install nose virtualenv>=1.7 scripttest>=1.1.1 mock --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
apt-get update && apt-get install -y ca-certificates && wget https://bootstrap.pypa.io/pip/2.7/get-pip.py && python2.7 get-pip.py && pip2.7 install nose virtualenv>=1.7 scripttest>=1.1.1 mock
###ACTION_DELIMITER###
deactivate && python2.7 -m pip install nose virtualenv>=1.7 scripttest>=1.1.1 mock
###ACTION_DELIMITER###
python2.7 -m pip list
###ACTION_DELIMITER###
python2.7 -m pip install nose==1.3.7 virtualenv==16.7.10 scripttest==1.3 mock==2.0.0
###ACTION_DELIMITER###
python2.7 -m pip install --index-url https://pypi.org/simple/ nose virtualenv>=1.7 scripttest>=1.1.1 mock
###ACTION_DELIMITER###
python2.7 -m pip install -e ".[testing]" --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
python2.7 -m pip install --upgrade setuptools==44.1.1 && python2.7 -m pip install -e ".[testing]" --index-url https://pypi.org/simple/
###ACTION_DELIMITER###
python2.7 -m pip install --index-url https://pypi.org/simple/ --upgrade setuptools==44.1.1 && python2.7 -m pip install --index-url https://pypi.org/simple/ nose virtualenv>=1.7 scripttest>=1.1.1 mock
###ACTION_DELIMITER###
python2.7 -m pip install --index-url https://pypi.org/simple/ nose==1.3.7 virtualenv==16.7.10 scripttest==1.3 mock==2.0.0
###ACTION_DELIMITER###
echo 'python setup.py test -v' > test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
python setup.py test -v

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
python setup.py test -v

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
python setup.py test -v

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
RUN git clone https://github.com/pypa/pip.git /home/pip

WORKDIR /home/pip
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("pypa", "pip_1_2")
class PIP_1_2(Instance):
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
        lines = log.split('\n')
        same_line_pattern = re.compile(r'^(tests\..*?) \.\.\. (ok|ERROR|skipped)$')
        test_name_pattern = re.compile(r'^tests\..*$')
        status_pattern = re.compile(r'.* \.\.\. (ok|ERROR|skipped)$')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Check same-line pattern first
            same_line_match = same_line_pattern.match(line)
            if same_line_match:
                test_name = same_line_match.group(1)
                status = same_line_match.group(2)
                if status == 'ok':
                    passed_tests.add(test_name)
                elif status == 'ERROR':
                    failed_tests.add(test_name)
                elif status == 'skipped':
                    skipped_tests.add(test_name)
                i += 1
                continue
            # Check if current line is a test name, then check next line for status
            test_name_match = test_name_pattern.match(line)
            if test_name_match and i + 1 < len(lines):
                next_line = lines[i+1].strip()
                status_match = status_pattern.match(next_line)
                if status_match:
                    test_name = test_name_match.group(0)
                    status = status_match.group(1)
                    if status == 'ok':
                        passed_tests.add(test_name)
                    elif status == 'ERROR':
                        failed_tests.add(test_name)
                    elif status == 'skipped':
                        skipped_tests.add(test_name)
                    i += 2  # skip next line as we processed it
                    continue
            # If neither, move to next line
            i += 1
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
