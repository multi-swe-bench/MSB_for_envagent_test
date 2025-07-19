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
        return "python:3.9-slim-bullseye"
    
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
pip3 --version
###ACTION_DELIMITER###
cat Makefile
###ACTION_DELIMITER###
pip3 install tox
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
apt-get update && apt-get install -y build-essential
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
###ACTION_DELIMITER###
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc && echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && echo 'eval "$(pyenv init -)"' >> ~/.bashrc && source ~/.bashrc
###ACTION_DELIMITER###
pyenv --version
###ACTION_DELIMITER###
apt-get install -y libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl
###ACTION_DELIMITER###
pyenv install 2.7.18
###ACTION_DELIMITER###
pyenv install 3.5.10
###ACTION_DELIMITER###
pyenv install 3.6.15
###ACTION_DELIMITER###
pyenv install 3.7.17
###ACTION_DELIMITER###
pyenv rehash && pyenv versions
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
pyenv local 2.7.18 3.5.10 3.6.15 3.7.17
###ACTION_DELIMITER###
echo $PATH && python2.7 --version && python3.5 --version && python3.6 --version && python3.7 --version
###ACTION_DELIMITER###
echo -e '[testenv:py27]\nbasepython = python2.7\n[testenv:py35]\nbasepython = python3.5\n[testenv:py36]\nbasepython = python3.6\n[testenv:py37]\nbasepython = python3.7' >> tox.ini
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
sed -i 's/deps=pipenv/deps=pip<23.0 pipenv/' tox.ini
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
source ~/.bashrc && make test
###ACTION_DELIMITER###
sed -i 's/deps=./pip<23.0 pipenv/deps=pip<23.0, pipenv/' tox.ini
###ACTION_DELIMITER###
sed -i 's|deps=pip<23.0 pipenv|deps=pip<23.0, pipenv|' tox.ini
###ACTION_DELIMITER###
sed -i 's/deps=pip<23.0, pipenv/deps=pip<23.0\n    pipenv/' tox.ini
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
cat .python-version
###ACTION_DELIMITER###
sed -i '/\[testenv\]/a deps=pip<23.0\n    pipenv' tox.ini && sed -i '/deps=pipenv/d' tox.ini && echo -e '[testenv:py27]\nbasepython = /root/.pyenv/versions/2.7.18/bin/python2.7\n[testenv:py35]\nbasepython = /root/.pyenv/versions/3.5.10/bin/python3.5\n[testenv:py36]\nbasepython = /root/.pyenv/versions/3.6.15/bin/python3.6\n[testenv:py37]\nbasepython = /root/.pyenv/versions/3.7.17/bin/python3.7' >> tox.ini
###ACTION_DELIMITER###
cat tox.ini
###ACTION_DELIMITER###
sed -i '/deps=pip<23.0\n    pipenv/d' tox.ini && sed -i '/\[testenv:py27\]/,/basepython = python2.7/d' tox.ini && sed -i '/\[testenv:py35\]/,/basepython = python3.5/d' tox.ini && sed -i '/\[testenv:py36\]/,/basepython = python3.6/d' tox.ini && sed -i '/\[testenv:py37\]/,/basepython = python3.7/d' tox.ini
###ACTION_DELIMITER###
cat tox.ini
###ACTION_DELIMITER###
sed -i '2,/deps=pip<23.0/d' tox.ini && echo -e '[testenv:py27]\nbasepython = /root/.pyenv/versions/2.7.18/bin/python2.7\n[testenv:py35]\nbasepython = /root/.pyenv/versions/3.5.10/bin/python3.5\n[testenv:py36]\nbasepython = /root/.pyenv/versions/3.6.15/bin/python3.6\n[testenv:py37]\nbasepython = /root/.pyenv/versions/3.7.17/bin/python3.7' >> tox.ini
###ACTION_DELIMITER###
sed -i 's/deps=pip<23.0\n    pipenv//' tox.ini && sed -i '/deps=pip<23.0\n    pipenv/d' tox.ini && echo -e 'deps=pip<23.0\n    pipenv' >> tox.ini && echo -e '[testenv:py27]\nbasepython = /root/.pyenv/versions/2.7.18/bin/python2.7\n[testenv:py35]\nbasepython = /root/.pyenv/versions/3.5.10/bin/python3.5\n[testenv:py36]\nbasepython = /root/.pyenv/versions/3.6.15/bin/python3.6\n[testenv:py37]\nbasepython = /root/.pyenv/versions/3.7.17/bin/python3.7' >> tox.ini
###ACTION_DELIMITER###
echo -e '[tox]\nenvlist = py27,py35,py36,py37\n\n[testenv]\ndeps = pip<23.0\n    pipenv\nsetenv = PIPENV_VERBOSITY=-1\ncommands=\n  pipenv install --dev --ignore-pipfile --skip-lock\n  pipenv run pytest -vv --cov-report term --cov-report html --cov cekit --basetemp={envtmpdir} --junit-xml target/junit-{envname}.xml --junit-prefix {envname} {posargs}\n\n[testenv:py27]\nbasepython = /root/.pyenv/versions/2.7.18/bin/python2.7\n\n[testenv:py35]\nbasepython = /root/.pyenv/versions/3.5.10/bin/python3.5\n\n[testenv:py36]\nbasepython = /root/.pyenv/versions/3.6.15/bin/python3.6\n\n[testenv:py37]\nbasepython = /root/.pyenv/versions/3.7.17/bin/python3.7' > tox.ini
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
pip3 uninstall -y tox && pip3 install tox==3.28.0 virtualenv==16.7.10
###ACTION_DELIMITER###
pip3 install --force-reinstall tox==3.28.0 virtualenv==16.7.10
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
rm -rf .tox && make test
###ACTION_DELIMITER###
echo 'tox --verbose' > test_commands.sh && chmod +x test_commands.sh && bash test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
tox --verbose

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
tox --verbose

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
tox --verbose

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
FROM python:3.9-slim-bullseye

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
RUN git clone https://github.com/cekit/cekit.git /home/cekit

WORKDIR /home/cekit
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("cekit", "cekit_3_3_1")
class CEKIT_3_3_1(Instance):
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
        import re, sys
        # Implement the log parsing logic here
        pattern = r'tests/[^:]+::(\S+)\s+(PASSED|FAILED|SKIPPED)\s+\['
        try:
            matches = re.findall(pattern, log)
        except re.error as e:
            print(f"Regex error: {e}", file=sys.stderr)
            return {"passed_tests": passed_tests, "failed_tests": failed_tests, "skipped_tests": skipped_tests}
        for test_name, status in matches:
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
