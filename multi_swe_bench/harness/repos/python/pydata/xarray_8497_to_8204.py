import re

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
        return "python:3.11-slim-bookworm"
    
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
ls -F ci/requirements
###ACTION_DELIMITER###
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O miniforge.sh
###ACTION_DELIMITER###
curl -L https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -o miniforge.sh
###ACTION_DELIMITER###
pip install .
###ACTION_DELIMITER###
ls -F ci
###ACTION_DELIMITER###
pip install .[complete]
###ACTION_DELIMITER###
python -m pytest
###ACTION_DELIMITER###
pip install pytest
###ACTION_DELIMITER###
python -m pytest
###ACTION_DELIMITER###
pip install "numpy<2"
###ACTION_DELIMITER###
python -m pytest
###ACTION_DELIMITER###
ls -F
###ACTION_DELIMITER###
pip list
###ACTION_DELIMITER###
echo '' > requirements.txt
###ACTION_DELIMITER###
echo 'boto3==1.24' >> requirements.txt
###ACTION_DELIMITER###
echo 'bottleneck==1.3' >> requirements.txt
###ACTION_DELIMITER###
echo 'cartopy==0.20' >> requirements.txt
echo 'cftime==1.6' >> requirements.txt
echo 'dask-core==2022.7' >> requirements.txt
echo 'distributed==2022.7' >> requirements.txt
echo 'flox==0.5' >> requirements.txt
echo 'h5netcdf==1.1' >> requirements.txt
echo 'h5py==3.7' >> requirements.txt
echo 'iris==3.2' >> requirements.txt
echo 'lxml==4.9' >> requirements.txt
echo 'matplotlib-base==3.5' >> requirements.txt
echo 'nc-time-axis==1.4' >> requirements.txt
echo 'netcdf4==1.6.0' >> requirements.txt
echo 'numba==0.55' >> requirements.txt
echo 'numpy==1.22' >> requirements.txt
echo 'packaging==21.3' >> requirements.txt
echo 'pandas==1.4' >> requirements.txt
echo 'pint==0.22' >> requirements.txt
echo 'pydap==3.3' >> requirements.txt
echo 'rasterio==1.3' >> requirements.txt
echo 'scipy==1.8' >> requirements.txt
echo 'seaborn==0.11' >> requirements.txt
echo 'sparse==0.13' >> requirements.txt
echo 'toolz==0.12' >> requirements.txt
echo 'typing_extensions==4.3' >> requirements.txt
echo 'zarr==2.12' >> requirements.txt
echo 'numbagg==0.2.1' >> requirements.txt
###ACTION_DELIMITER###
echo 'coveralls' >> requirements.txt
echo 'hypothesis' >> requirements.txt
echo 'pytest' >> requirements.txt
echo 'pytest-cov' >> requirements.txt
echo 'pytest-env' >> requirements.txt
echo 'pytest-xdist' >> requirements.txt
echo 'pytest-timeout' >> requirements.txt
###ACTION_DELIMITER###

###ACTION_DELIMITER###
pip install -r requirements.txt
###ACTION_DELIMITER###
echo '' > requirements.txt
###ACTION_DELIMITER###
echo 'pytest' >> requirements.txt
echo 'pytest-cov' >> requirements.txt
echo 'pytest-env' >> requirements.txt
echo 'pytest-xdist' >> requirements.txt
echo 'pytest-timeout' >> requirements.txt
###ACTION_DELIMITER###
echo 'boto3==1.24' >> requirements.txt
echo 'cartopy==0.20' >> requirements.txt
echo 'cftime==1.6' >> requirements.txt
echo 'dask-core==2022.7' >> requirements.txt
echo 'distributed==2022.7' >> requirements.txt
echo 'flox==0.5' >> requirements.txt
echo 'h5netcdf==1.1' >> requirements.txt
echo 'h5py==3.7' >> requirements.txt
echo 'iris==3.2' >> requirements.txt
echo 'lxml==4.9' >> requirements.txt
echo 'matplotlib-base==3.5' >> requirements.txt
echo 'nc-time-axis==1.4' >> requirements.txt
echo 'netcdf4==1.6.0' >> requirements.txt
echo 'numba==0.55' >> requirements.txt
echo 'numpy==1.22' >> requirements.txt
echo 'packaging==21.3' >> requirements.txt
echo 'pandas==1.4' >> requirements.txt
echo 'pint==0.22' >> requirements.txt
echo 'pydap==3.3' >> requirements.txt
echo 'rasterio==1.3' >> requirements.txt
echo 'scipy==1.8' >> requirements.txt
echo 'seaborn==0.11' >> requirements.txt
echo 'sparse==0.13' >> requirements.txt
echo 'toolz==0.12' >> requirements.txt
echo 'typing_extensions==4.3' >> requirements.txt
echo 'zarr==2.12' >> requirements.txt
echo 'numbagg==0.2.1' >> requirements.txt
###ACTION_DELIMITER###
sed -i '/bottleneck/d' requirements.txt
###ACTION_DELIMITER###
pip install -r requirements.txt
###ACTION_DELIMITER###
apt-get update && apt-get install -y curl
###ACTION_DELIMITER###
curl -L https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -o miniforge.sh
###ACTION_DELIMITER###
bash miniforge.sh -b -p $HOME/conda
###ACTION_DELIMITER###
source $HOME/conda/bin/activate && conda env create -f ci/requirements/min-all-deps.yml
###ACTION_DELIMITER###
source $HOME/conda/bin/activate xarray-tests && pip install -e .
###ACTION_DELIMITER###
source $HOME/conda/bin/activate xarray-tests && python -m pytest
###ACTION_DELIMITER###
echo 'source $HOME/conda/bin/activate xarray-tests && python -m pytest --verbose' > test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
source $HOME/conda/bin/activate xarray-tests && python -m pytest --verbose

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
source $HOME/conda/bin/activate xarray-tests && python -m pytest --verbose

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
source $HOME/conda/bin/activate xarray-tests && python -m pytest --verbose

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
FROM python:3.11-slim-bookworm

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


@Instance.register("pydata", "xarray_8497_to_8204")
class XARRAY_8497_TO_8204(Instance):
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
        test_results = {} 
        test_line_pattern = re.compile(r"^(xarray/tests/.*?)\s+(PASSED|FAILED|SKIPPED|XFAIL|XPASS)")
        failed_summary_pattern = re.compile(r"^FAILED\s+(xarray/tests/.*?)(?:\s+-|$)")
        for line in log.splitlines():
            match = test_line_pattern.match(line)
            if match:
                test_name, status = match.groups()
                test_name = test_name.strip()
                if test_name not in test_results or test_results[test_name] != "FAILED":
                     test_results[test_name] = status
        summary_section = False
        for line in log.splitlines():
            if "short test summary info" in line:
                summary_section = True
            if summary_section:
                match = failed_summary_pattern.match(line)
                if match:
                    test_name = match.group(1).strip()
                    test_results[test_name] = "FAILED"
        passed_tests = {test for test, status in test_results.items() if status in ("PASSED", "XPASS")}
        failed_tests = {test for test, status in test_results.items() if status == "FAILED"}
        skipped_tests = {test for test, status in test_results.items() if status in ("SKIPPED", "XFAIL")}
        parsed_results = {
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
        }
        

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
