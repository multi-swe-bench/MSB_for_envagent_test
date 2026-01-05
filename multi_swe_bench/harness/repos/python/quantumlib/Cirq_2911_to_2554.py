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
        return "ubuntu:20.04"
    
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
                """ls -la
###ACTION_DELIMITER###
apt-get update && apt-get install -y $(cat apt-system-requirements.txt)
###ACTION_DELIMITER###
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
###ACTION_DELIMITER###
apt-get install -y python3 python3-pip
###ACTION_DELIMITER###
pip3 install --upgrade pip setuptools wheel && pip3 install -r requirements.txt
###ACTION_DELIMITER###
cat requirements.txt | xargs -n 1 pip3 install
###ACTION_DELIMITER###
grep -v '^#\|^$' requirements.txt | xargs -n 1 pip3 install
###ACTION_DELIMITER###
pip3 install --upgrade pip setuptools wheel && pip3 install -r requirements.txt --break-system-packages
###ACTION_DELIMITER###
pip3 install --upgrade pip setuptools wheel && pip3 install -r requirements.txt
###ACTION_DELIMITER###
pip3 install google-api-core[grpc]==1.19.0 && pip3 install -r requirements.txt
###ACTION_DELIMITER###
pip3 check
###ACTION_DELIMITER###
pip3 uninstall -y googleapis-common-protos grpcio-status proto-plus && pip3 install googleapis-common-protos==1.56.0 grpcio-status==1.34.0 proto-plus==1.18.0
###ACTION_DELIMITER###
pip3 install protobuf==3.8.0 && pip3 check
###ACTION_DELIMITER###
pip3 uninstall -y googleapis-common-protos proto-plus grpcio-status && pip3 install googleapis-common-protos==1.52.0 proto-plus==1.7.1 grpcio-status==1.30.0 && pip3 check
###ACTION_DELIMITER###
apt-get install -y python3-cairo && pip3 uninstall -y proto-plus && pip3 install proto-plus==1.4.0 && pip3 check
###ACTION_DELIMITER###
pip3 install -r dev_tools/conf/pip-list-dev-tools.txt --break-system-packages
###ACTION_DELIMITER###
pip3 install -r dev_tools/conf/pip-list-dev-tools.txt
###ACTION_DELIMITER###
pip3 install mypy~=0.701.0
###ACTION_DELIMITER###
pip3 install mypy~=0.780.0
###ACTION_DELIMITER###
pip3 install pylint~=2.3.0 astroid~=2.1.0
###ACTION_DELIMITER###
pip3 install pylint~=2.3.0 astroid~=2.2.0
###ACTION_DELIMITER###
pip3 install pytest~=5.4.1 pytest-asyncio~=0.10.0 pytest-cov~=2.5.0 pytest-benchmark~=3.2.0
###ACTION_DELIMITER###
pip3 install yapf~=0.27.0
###ACTION_DELIMITER###
pip3 install grpcio-tools~=1.24.0 mypy-protobuf==1.10
###ACTION_DELIMITER###
pip3 install twine
###ACTION_DELIMITER###
pytest -v --no-header -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v --no-header -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
pip3 install protobuf==3.20.3 && PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v --no-header -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
pip3 install numpy==1.16.6 && PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
pip3 install numpy==1.17.5 && PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
pip3 install numpy==1.21.6 && PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
pip3 install pyparsing && pip3 install numpy==1.21.6 && PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
pip3 install qiskit~=0.13.0 && PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
pip3 install qiskit-aer==0.3.1 && pip3 install qiskit~=0.13.0 && PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
apt-get update && apt-get install -y cmake && pip3 install qiskit-aer==0.3.1 && pip3 install qiskit~=0.13.0 && PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
apt-get install -y g++ libopenblas-dev libomp-dev && pip3 install qiskit-aer==0.3.1 && pip3 install qiskit~=0.13.0 && PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
pip3 install qiskit-aer==0.3.0 && pip3 install qiskit~=0.13.0 && PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider cirq/
###ACTION_DELIMITER###
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider -k 'not qasm' cirq/
###ACTION_DELIMITER###
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider --ignore=cirq/contrib/qasm_import/ cirq/
###ACTION_DELIMITER###

###ACTION_DELIMITER###
echo 'PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider --ignore=cirq/contrib/qasm_import/ cirq/' > /home/Cirq/test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider --ignore=cirq/contrib/qasm_import/ cirq/

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
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider --ignore=cirq/contrib/qasm_import/ cirq/

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
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python pytest -v -rA --tb=no -p no:cacheprovider --ignore=cirq/contrib/qasm_import/ cirq/

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

# Choose an appropriate base image based on the project's requirements - replace ubuntu:20.04 with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM ubuntu:20.04

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


@Instance.register("quantumlib", "Cirq_2911_to_2554")
class CIRQ_2911_TO_2554(Instance):
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
        passed_tests = set[str]()
        failed_tests = set[str]()
        skipped_tests = set[str]()
        import re
        lines = log.split('\n')
        for line in lines:
            line = line.strip()
            # Match test lines with format: 'test_name STATUS' or 'STATUS test_name'
            match1 = re.match(r'.*?(.+?)\s+(PASSED|FAILED|SKIPPED).*', line)
            match2 = re.match(r'^(PASSED|FAILED|SKIPPED)\s+(.+?)$', line)
            if match1:
                test_name = match1.group(1)
                status = match1.group(2)
            elif match2:
                status = match2.group(1)
                test_name = match2.group(2)
            else:
                continue
            # Add to appropriate set
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
