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
        return "continuumio/miniconda3"
    
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
                """ls -F
###ACTION_DELIMITER###
ls -F ci/
###ACTION_DELIMITER###
ls -F ci/requirements/
###ACTION_DELIMITER###
conda env create -f ci/requirements/environment.yml
###ACTION_DELIMITER###
conda init bash
source ~/.bashrc
conda activate xarray-tests
pip install --no-deps -e .
###ACTION_DELIMITER###
pytest --no-header -rA --tb=no -p no:cacheprovider
###ACTION_DELIMITER###
sed -i 's/numpy/numpy<2.0/' ci/requirements/environment.yml
###ACTION_DELIMITER###
conda env create -f ci/requirements/environment.yml
###ACTION_DELIMITER###
conda env update -f ci/requirements/environment.yml --prune
###ACTION_DELIMITER###
conda env remove -n xarray-tests
###ACTION_DELIMITER###
rm -rf /opt/conda/envs/xarray-tests
###ACTION_DELIMITER###
conda env create -f ci/requirements/environment.yml
###ACTION_DELIMITER###
rm -rf /opt/conda/envs/xarray-tests
###ACTION_DELIMITER###
conda env create -f ci/requirements/py37-min-all-deps.yml
###ACTION_DELIMITER###
conda init bash
source ~/.bashrc
conda activate xarray-tests
pip install --no-deps -e .
###ACTION_DELIMITER###
pytest --no-header -rA --tb=no -p no:cacheprovider
###ACTION_DELIMITER###
echo "conda init bash
source ~/.bashrc
conda activate xarray-tests
pytest --no-header -rA --tb=no -p no:cacheprovider" > test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
conda init bash
source ~/.bashrc
conda activate xarray-tests
pytest --no-header -rA --tb=no -p no:cacheprovider

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
conda init bash
source ~/.bashrc
conda activate xarray-tests
pytest --no-header -rA --tb=no -p no:cacheprovider

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
conda init bash
source ~/.bashrc
conda activate xarray-tests
pytest --no-header -rA --tb=no -p no:cacheprovider

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
FROM continuumio/miniconda3

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
RUN git clone https://github.com/pydata/xarray.git /home/xarray

WORKDIR /home/xarray
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("pydata", "xarray_5227_to_4871")
class XARRAY_5227_TO_4871(Instance):
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
        for line in log.splitlines():
            if line.startswith("PASSED"):
                match = re.search(r"^PASSED\s+(.*)", line)
                if match:
                    passed_tests.add(match.group(1).strip())
            elif line.startswith("FAILED"):
                match = re.search(r"^FAILED\s+(.*?)(?:\s+-.*)?$", line)
                if match:
                    failed_tests.add(match.group(1).strip())
            elif line.startswith("SKIPPED"):
                match = re.search(r"^SKIPPED\s+\[\d+\]\s+([^:]+)", line)
                if match:
                    skipped_tests.add(match.group(1).strip())
            elif "XPASS" in line:
                match = re.search(r"^XPASS\s+([^\s]+)", line)
                if match:
                    passed_tests.add(match.group(1).strip())
            elif "XFAIL" in line:
                match = re.search(r"^XFAIL\s+([^\s]+)", line)
                if match:
                    skipped_tests.add(match.group(1).strip())
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
