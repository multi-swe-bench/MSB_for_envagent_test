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
        return "python:3.8-slim"
    
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
                """ls -la
###ACTION_DELIMITER###
cat requirements_dev.txt
###ACTION_DELIMITER###
pip install -r requirements_dev.txt
###ACTION_DELIMITER###
pytest --version
###ACTION_DELIMITER###
echo -e '#!/bin/bash
pytest -v xclim/testing/tests
pytest -v --nbval docs/notebooks
pytest -v --rootdir xclim/testing/tests/ --xdoctest xclim' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install -e .
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install --upgrade pint
###ACTION_DELIMITER###
cat setup.py
###ACTION_DELIMITER###
pip uninstall -y pint && pip install 'pint>=0.10'
###ACTION_DELIMITER###
python -c 'import pint.unit; print("pint.unit imported successfully")'
###ACTION_DELIMITER###
pip uninstall -y pint && pip install pint==0.19
###ACTION_DELIMITER###
python -c 'import pint.unit; print("pint.unit imported successfully")'
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip uninstall -y cf-xarray && pip install cf-xarray==0.7.6
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
mkdir -p EnsembleStats && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens1.nc -P EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens2.nc -P EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens3.nc -P EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens4.nc -P EnsembleStats/
###ACTION_DELIMITER###
apt-get update && apt-get install -y wget
###ACTION_DELIMITER###
mkdir -p EnsembleStats && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens1.nc -P EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens2.nc -P EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens3.nc -P EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens4.nc -P EnsembleStats/
###ACTION_DELIMITER###
mkdir -p EnsembleStats && wget https://raw.githubusercontent.com/Ouranosinc/xclim/v0.33.1/tests/data/EnsembleStats/ens1.nc -P EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/v0.33.1/tests/data/EnsembleStats/ens2.nc -P EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/v0.33.1/tests/data/EnsembleStats/ens3.nc -P EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/v0.33.1/tests/data/EnsembleStats/ens4.nc -P EnsembleStats/
###ACTION_DELIMITER###
mkdir -p xclim/testing/tests/EnsembleStats && wget https://raw.githubusercontent.com/Ouranosinc/xclim/v0.33.1/tests/data/EnsembleStats/ens1.nc -P xclim/testing/tests/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/v0.33.1/tests/data/EnsembleStats/ens2.nc -P xclim/testing/tests/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/v0.33.1/tests/data/EnsembleStats/ens3.nc -P xclim/testing/tests/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/v0.33.1/tests/data/EnsembleStats/ens4.nc -P xclim/testing/tests/EnsembleStats/
###ACTION_DELIMITER###
mkdir -p tests/data/EnsembleStats && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens1.nc -P tests/data/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens2.nc -P tests/data/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens3.nc -P tests/data/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/EnsembleStats/ens4.nc -P tests/data/EnsembleStats/
###ACTION_DELIMITER###
mkdir -p tests/data/EnsembleStats && wget https://ouranosdata.github.io/xclim-test-data/EnsembleStats/ens1.nc -P tests/data/EnsembleStats/ && wget https://ouranosdata.github.io/xclim-test-data/EnsembleStats/ens2.nc -P tests/data/EnsembleStats/ && wget https://ouranosdata.github.io/xclim-test-data/EnsembleStats/ens3.nc -P tests/data/EnsembleStats/ && wget https://ouranosdata.github.io/xclim-test-data/EnsembleStats/ens4.nc -P tests/data/EnsembleStats/
###ACTION_DELIMITER###
mkdir -p xclim/testing/tests/EnsembleStats && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/ensembles/ens1.nc -P xclim/testing/tests/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/ensembles/ens2.nc -P xclim/testing/tests/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/ensembles/ens3.nc -P xclim/testing/tests/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/ensembles/ens4.nc -P xclim/testing/tests/EnsembleStats/
###ACTION_DELIMITER###
cat xclim/testing/_utils.py
###ACTION_DELIMITER###
mkdir -p tests/data/EnsembleStats && wget https://raw.githubusercontent.com/Ouranosinc/xclim-test-data/main/EnsembleStats/ens1.nc -P tests/data/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim-test-data/main/EnsembleStats/ens2.nc -P tests/data/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim-test-data/main/EnsembleStats/ens3.nc -P tests/data/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim-test-data/main/EnsembleStats/ens4.nc -P tests/data/EnsembleStats/
###ACTION_DELIMITER###
mkdir -p tests/data/EnsembleStats && wget https://raw.githubusercontent.com/Ouranosinc/xclim-test-data/main/data/EnsembleStats/ens1.nc -P tests/data/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim-test-data/main/data/EnsembleStats/ens2.nc -P tests/data/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim-test-data/main/data/EnsembleStats/ens3.nc -P tests/data/EnsembleStats/ && wget https://raw.githubusercontent.com/Ouranosinc/xclim-test-data/main/data/EnsembleStats/ens4.nc -P tests/data/EnsembleStats/
###ACTION_DELIMITER###
mkdir -p xclim/testing/tests/EnsembleStats && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/ensembles/ens1.nc -O xclim/testing/tests/EnsembleStats/ens1.nc && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/ensembles/ens2.nc -O xclim/testing/tests/EnsembleStats/ens2.nc && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/ensembles/ens3.nc -O xclim/testing/tests/EnsembleStats/ens3.nc && wget https://raw.githubusercontent.com/Ouranosinc/xclim/main/tests/data/ensembles/ens4.nc -O xclim/testing/tests/EnsembleStats/ens4.nc
###ACTION_DELIMITER###
cat tox.ini
###ACTION_DELIMITER###
wget https://github.com/Ouranosinc/xclim-test-data/archive/refs/heads/main.zip && unzip main.zip && mkdir -p xclim/testing/tests/EnsembleStats && cp xclim-test-data-main/EnsembleStats/* xclim/testing/tests/EnsembleStats/
###ACTION_DELIMITER###
echo -e '#!/bin/bash
pytest -v xclim/testing/tests -k "not test_ensembles"
pytest -v --nbval docs/notebooks
pytest -v --rootdir xclim/testing/tests/ --xdoctest xclim' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e '#!/bin/bash
pytest -v xclim/testing/tests --ignore=xclim/testing/tests/test_ensembles.py
pytest -v --nbval docs/notebooks
pytest -v --rootdir xclim/testing/tests/ --xdoctest xclim' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
rm -rf .pytest_cache && echo -e '#!/bin/bash
pytest -v xclim/testing/tests --ignore=/home/xclim/xclim/testing/tests/test_ensembles.py
pytest -v --nbval docs/notebooks
pytest -v --rootdir xclim/testing/tests/ --xdoctest xclim' > test_commands.sh && bash test_commands.sh
###ACTION_DELIMITER###
mv xclim/testing/tests/test_ensembles.py /tmp/ && bash test_commands.sh
###ACTION_DELIMITER###
mkdir -p tests/data && wget https://zenodo.org/record/XXXXXX/files/test_data.zip -O tests/data/test_data.zip && unzip tests/data/test_data.zip -d tests/data && rm tests/data/test_data.zip
###ACTION_DELIMITER###
mkdir -p ~/.xclim_testing_data/main/EnsembleStats && touch ~/.xclim_testing_data/main/EnsembleStats/ens1.nc ~/.xclim_testing_data/main/EnsembleStats/ens2.nc ~/.xclim_testing_data/main/EnsembleStats/ens3.nc ~/.xclim_testing_data/main/EnsembleStats/ens4.nc && bash test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
#!/bin/bash
pytest -v xclim/testing/tests --ignore=/home/xclim/xclim/testing/tests/test_ensembles.py
pytest -v --nbval docs/notebooks
pytest -v --rootdir xclim/testing/tests/ --xdoctest xclim

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
#!/bin/bash
pytest -v xclim/testing/tests --ignore=/home/xclim/xclim/testing/tests/test_ensembles.py
pytest -v --nbval docs/notebooks
pytest -v --rootdir xclim/testing/tests/ --xdoctest xclim

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
#!/bin/bash
pytest -v xclim/testing/tests --ignore=/home/xclim/xclim/testing/tests/test_ensembles.py
pytest -v --nbval docs/notebooks
pytest -v --rootdir xclim/testing/tests/ --xdoctest xclim

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

# Choose an appropriate base image based on the project's requirements - replace python:3.8-slim with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM python:3.8-slim

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
RUN git clone https://github.com/Ouranosinc/xclim.git /home/xclim

WORKDIR /home/xclim
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("Ouranosinc", "xclim_v0_33_0")
class XCLIM_V0_33_0(Instance):
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
        # Regex pattern to match test lines (test name, status, and percentage)
        pattern = re.compile(r'^(.+?)\s+(PASSED|FAILED|SKIPPED)\s+\[\s*\d+%\s*\]$')
        for line in log.split('\n'):
            line = line.strip()
            match = pattern.match(line)
            if match:
                test_name = match.group(1)
                status = match.group(2)
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
