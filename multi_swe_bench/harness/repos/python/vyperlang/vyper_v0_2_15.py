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
        return "ubuntu:latest"
    
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
                """apt-get update && apt-get install -y build-essential python3.10 python3.10-venv python3.10-dev libsha3-dev libb2-dev
###ACTION_DELIMITER###
apt-get update && apt-get install -y build-essential python3 python3-venv python3-dev libb2-dev
###ACTION_DELIMITER###
python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install .[test]
###ACTION_DELIMITER###
source venv/bin/activate && pip install Cython && pip install --upgrade setuptools && pip install .[test]
###ACTION_DELIMITER###
source venv/bin/activate && pip install Cython==0.29.36 && pip install cytoolz && pip install .[test]
###ACTION_DELIMITER###
source venv/bin/activate && pip install cytoolz==0.12.0 && pip install .[test]
###ACTION_DELIMITER###
apt-get update && apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa -y && apt-get update && apt-get install -y python3.10 python3.10-venv python3.10-dev
###ACTION_DELIMITER###
python3.10 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install .[test]
###ACTION_DELIMITER###
source venv/bin/activate && pip install blake2b-py && pip install .[test]
###ACTION_DELIMITER###
source venv/bin/activate && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && source $HOME/.cargo/env && rustup default nightly && pip install blake2b-py && pip install .[test]
###ACTION_DELIMITER###
source venv/bin/activate && apt-get update && apt-get install -y curl && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && source $HOME/.cargo/env && rustup default nightly && pip install blake2b-py && pip install .[test]
###ACTION_DELIMITER###
echo 'pytest --no-header -rA --tb=no -p no:cacheprovider' > /home/vyper/test_commands.sh
###ACTION_DELIMITER###
bash /home/vyper/test_commands.sh
###ACTION_DELIMITER###
source venv/bin/activate && pip install --force-reinstall pytest==5.4.3 && echo 'pytest -v' > /home/vyper/test_commands.sh && bash /home/vyper/test_commands.sh
###ACTION_DELIMITER###
source venv/bin/activate && echo 'pytest -v -p no:plugins' > /home/vyper/test_commands.sh && bash /home/vyper/test_commands.sh
###ACTION_DELIMITER###
source venv/bin/activate && echo 'pytest -v --assert=plain' > /home/vyper/test_commands.sh && bash /home/vyper/test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest -v --assert=plain
(venv) (venv) 
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
pytest -v --assert=plain
(venv) (venv) 
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
pytest -v --assert=plain
(venv) (venv) 
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

# Choose an appropriate base image based on the project's requirements - replace ubuntu:latest with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM ubuntu:latest

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
RUN git clone https://github.com/vyperlang/vyper.git /home/vyper

WORKDIR /home/vyper
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("vyperlang", "vyper_v0_2_15")
class VYPER_V0_2_15(Instance):
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
        pass
