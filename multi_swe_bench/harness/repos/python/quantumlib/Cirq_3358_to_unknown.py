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
        return "ubuntu"
    
    def image_prefix(self) -> str:
        return "envagent"
       
    def image_tag(self) -> str:
        return f"pr-{self.pr.number}"

    def workdir(self) -> str:
        return f"pr-{self.pr.number}"

    def files(self) -> list[File]:
        repo_name= self.pr.repo
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
                """cat .github/workflows/ci.yml
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
apt-get install -y software-properties-common
###ACTION_DELIMITER###
add-apt-repository ppa:deadsnakes/ppa -y
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
apt-get install -y python3.7 python3.7-venv
###ACTION_DELIMITER###
python3.7 -m venv venv
###ACTION_DELIMITER###
source venv/bin/activate
###ACTION_DELIMITER###
pip install -r requirements.txt
###ACTION_DELIMITER###
pip install -r dev_tools/conf/pip-list-dev-tools.txt
###ACTION_DELIMITER###
cat dev_tools/conf/pip-list-dev-tools.txt | grep -v 'google-colab' | xargs pip install
###ACTION_DELIMITER###
cat dev_tools/conf/pip-list-dev-tools.txt | grep -vE '^#|google-colab' | xargs pip install
###ACTION_DELIMITER###
pip install setuptools==58.0.0
###ACTION_DELIMITER###
cat dev_tools/conf/pip-list-dev-tools.txt | grep -vE '^#|google-colab' | xargs pip install
###ACTION_DELIMITER###
pip install pytest~=5.4.1
###ACTION_DELIMITER###
pip install -r cirq/contrib/contrib-requirements.txt
###ACTION_DELIMITER###
apt-get install -y build-essential
###ACTION_DELIMITER###
pip install -r cirq/contrib/contrib-requirements.txt
###ACTION_DELIMITER###
apt-get install -y python3.7-dev
###ACTION_DELIMITER###
pip install -r cirq/contrib/contrib-requirements.txt
###ACTION_DELIMITER###
echo 'pytest -v --ignore=cirq/contrib --benchmark-skip' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pytest-benchmark~=3.2.0
###ACTION_DELIMITER###
bash test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
pytest -v --ignore=cirq/contrib --benchmark-skip

""".replace("[[REPO_NAME]]", repo_name)
            ),
            File(
                ".",
                "test-run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
if ! git -C /home/[[REPO_NAME]] apply --whitespace=nowarn /home/test.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
pytest -v --ignore=cirq/contrib --benchmark-skip

""".replace("[[REPO_NAME]]", repo_name)
            ),
            File(
                ".",
                "fix-run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
if ! git -C /home/[[REPO_NAME]] apply --whitespace=nowarn  /home/test.patch /home/fix.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
pytest -v --ignore=cirq/contrib --benchmark-skip

""".replace("[[REPO_NAME]]", repo_name)
            ),
        ]

    def dockerfile(self) -> str:
        copy_commands = ""
        for file in self.files():
            copy_commands += f"COPY {file.name} /home/\n"

        dockerfile_content = """
# This is a template for creating a Dockerfile to test patches
# LLM should fill in the appropriate values based on the context

# Choose an appropriate base image based on the project's requirements - replace ubuntu with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM ubuntu

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
RUN git clone https://github.com/quantumlib/Cirq.git /home/Cirq

WORKDIR /home/Cirq
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("quantumlib", "Cirq_3358_to_unknown")
class CIRQ_3358_TO_UNKNOWN(Instance):
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
        # Parse test statuses using regex patterns
        # Passed tests: e.g., 'cirq/_compat_test.py::test_proper_repr PASSED'
        passed_pattern = re.compile(r'([\w/]+\.py::[\w\[\]_\-\[\]]+) PASSED')
        passed_tests.update(passed_pattern.findall(log))
        # Failed tests: e.g., 'FAILED cirq/sim/simulator_test.py::test_async_sample'
        failed_pattern = re.compile(r'FAILED ([\w/]+\.py::[\w\[\]_\-\[\]]+)')
        failed_tests.update(failed_pattern.findall(log))
        # XFAIL tests: e.g., 'cirq/protocols/json_serialization_test.py::test_json_test_data_coverage[...] XFAIL'
        xfail_pattern = re.compile(r'([\w/]+\.py::[\w\[\]_\-\[\]]+) XFAIL')
        failed_tests.update(xfail_pattern.findall(log))  # XFAIL is treated as a failure
        # Skipped tests: e.g., 'cirq/foo/bar_test.py::test_skipped SKIPPED' (assumed pattern)
        skipped_pattern = re.compile(r'([\w/]+\.py::[\w\[\]_\-\[\]]+) SKIPPED')
        skipped_tests.update(skipped_pattern.findall(log))
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
