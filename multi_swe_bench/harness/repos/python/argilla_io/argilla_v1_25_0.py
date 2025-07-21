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
                """pip3.9 install -e '.[tests]'
###ACTION_DELIMITER###
python3.9 --version
###ACTION_DELIMITER###
add-apt-repository -y ppa:deadsnakes/ppa && apt-get update && apt-get install -y python3.9 python3.9-pip
###ACTION_DELIMITER###
apt-get update && apt-get install -y software-properties-common
###ACTION_DELIMITER###
add-apt-repository -y ppa:deadsnakes/ppa && apt-get update && apt-get install -y python3.9 python3.9-pip
###ACTION_DELIMITER###
apt-get update && apt-get install -y python3.9 && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.9 get-pip.py
###ACTION_DELIMITER###
apt-get install -y curl && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.9 get-pip.py
###ACTION_DELIMITER###
apt-get install -y python3.9-distutils && python3.9 get-pip.py
###ACTION_DELIMITER###
pip3.9 install -e '.[tests]'
###ACTION_DELIMITER###
echo 'pytest -vs tests/' > /home/argilla/test_commands.sh
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pip3.9 install -e '.[tests,server]'
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pip3.9 install cffi
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pip3.9 install -e '.[tests,server,integrations,listeners]'
###ACTION_DELIMITER###
bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
pip3.9 install 'setuptools<81' && bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
echo 'pytest -vs tests/ -k "not cli"' > /home/argilla/test_commands.sh && bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
sed -i 's/_, extra_value = dep.split(" ; extra ==")/parts = dep.split(" ; extra ==", 1); _ = parts[0]; extra_value = parts[1] if len(parts) > 1 else ""/' src/argilla/utils/dependency.py && bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
sed -i 's/if is_package_with_extras_installed("argilla", ["server"]):/if True:/' src/argilla/cli/app.py && bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
sed -i 's/if is_package_with_extras_installed("argilla", \["server"\]):/if True:/' src/argilla/cli/app.py && bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
sed -i 's/if is_package_with_extras_installed("argilla", \["server"\]):/if True:/' src/argilla/cli/app.py && echo 'pytest -vs tests/unit/client/sdk/models/test_datasets.py' > /home/argilla/test_commands.sh && bash /home/argilla/test_commands.sh
###ACTION_DELIMITER###
echo 'pytest -vs tests/unit/client/sdk/models/ -k "test_datasets or test_text_classification"' > /home/argilla/test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest -vs tests/unit/client/sdk/models/ -k "test_datasets or test_text_classification"

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
pytest -vs tests/unit/client/sdk/models/ -k "test_datasets or test_text_classification"

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
pytest -vs tests/unit/client/sdk/models/ -k "test_datasets or test_text_classification"

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
RUN git clone https://github.com/argilla-io/argilla.git /home/argilla

WORKDIR /home/argilla
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("argilla-io", "argilla_v1_25_0")
class ARGILLA_V1_25_0(Instance):
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
        lines = log.split('\n')
        current_test = None
        for line in lines:
            stripped_line = line.strip()
            # Check if the line contains a test name and possibly a status
            test_match = re.match(r'^(tests/.*?)(\s+PASSED|\s+FAILED|\s+SKIPPED)?$', stripped_line)
            if test_match:
                test_name = test_match.group(1)
                status = test_match.group(2)
                if status:
                    status = status.strip()
                    if status == 'PASSED':
                        passed_tests.add(test_name)
                    elif status == 'FAILED':
                        failed_tests.add(test_name)
                    elif status == 'SKIPPED':
                        skipped_tests.add(test_name)
                    current_test = None
                else:
                    current_test = test_name
            # Check if the line is a status for the current test
            elif current_test is not None:
                if stripped_line == 'PASSED':
                    passed_tests.add(current_test)
                    current_test = None
                elif stripped_line == 'FAILED':
                    failed_tests.add(current_test)
                    current_test = None
                elif stripped_line == 'SKIPPED':
                    skipped_tests.add(current_test)
                    current_test = None
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
