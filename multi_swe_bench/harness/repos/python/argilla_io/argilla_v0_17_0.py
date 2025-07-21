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
pip install spacy
###ACTION_DELIMITER###
apt-get update && apt-get install -y build-essential
###ACTION_DELIMITER###
pip install spacy
###ACTION_DELIMITER###
pytest -v tests/
###ACTION_DELIMITER###
pip install pytest
###ACTION_DELIMITER###
pytest -v tests/
###ACTION_DELIMITER###
pip install httpx~=0.15.0
###ACTION_DELIMITER###
pytest -v tests/
###ACTION_DELIMITER###
ls src
###ACTION_DELIMITER###
pip install -e .
###ACTION_DELIMITER###
pytest -v tests/
###ACTION_DELIMITER###
pip install -e .[server]
###ACTION_DELIMITER###
pytest -v tests/
###ACTION_DELIMITER###
pip install numpy==1.26.4
###ACTION_DELIMITER###
pip install spacy==3.5.4
###ACTION_DELIMITER###
pytest -v tests/
###ACTION_DELIMITER###
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add - && echo 'deb https://artifacts.elastic.co/packages/oss-7.x/apt stable main' | tee /etc/apt/sources.list.d/elastic.list && apt-get update && apt-get install -y elasticsearch-oss=7.10.2 && echo 'discovery.type: single-node' >> /etc/elasticsearch/elasticsearch.yml && /usr/share/elasticsearch/bin/elasticsearch -d
###ACTION_DELIMITER###
apt-get update && apt-get install -y wget
###ACTION_DELIMITER###
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add - && echo 'deb https://artifacts.elastic.co/packages/oss-7.x/apt stable main' | tee /etc/apt/sources.list.d/elastic.list && apt-get update && apt-get install -y elasticsearch-oss=7.10.2 && echo 'discovery.type: single-node' >> /etc/elasticsearch/elasticsearch.yml && /usr/share/elasticsearch/bin/elasticsearch -d
###ACTION_DELIMITER###
apt-get update && apt-get install -y procps && su - elasticsearch -c '/usr/share/elasticsearch/bin/elasticsearch -d'
###ACTION_DELIMITER###
mkdir -p /nonexistent && chown elasticsearch:elasticsearch /nonexistent && su - elasticsearch -c '/usr/share/elasticsearch/bin/elasticsearch -d'
###ACTION_DELIMITER###
curl http://localhost:9200
###ACTION_DELIMITER###
apt-get update && apt-get install -y curl
###ACTION_DELIMITER###
curl http://localhost:9200
###ACTION_DELIMITER###
tail -n 50 /var/log/elasticsearch/elasticsearch.log
###ACTION_DELIMITER###
mkdir -p /home/elasticsearch && chown elasticsearch:elasticsearch /home/elasticsearch && usermod -d /home/elasticsearch elasticsearch && su - elasticsearch -c '/usr/share/elasticsearch/bin/elasticsearch -d'
###ACTION_DELIMITER###
ps aux | grep elasticsearch && tail -n 50 /var/log/elasticsearch/elasticsearch.log
###ACTION_DELIMITER###
chown -R elasticsearch:elasticsearch /usr/share/elasticsearch /var/log/elasticsearch /home/elasticsearch && sudo -u elasticsearch /usr/share/elasticsearch/bin/elasticsearch -d
###ACTION_DELIMITER###
grep elasticsearch /etc/passwd && su - elasticsearch -c '/usr/share/elasticsearch/bin/elasticsearch -d'
###ACTION_DELIMITER###
usermod -s /bin/bash elasticsearch && su - elasticsearch -c '/usr/share/elasticsearch/bin/elasticsearch -d'
###ACTION_DELIMITER###
ps aux | grep elasticsearch && tail -n 50 /var/log/elasticsearch/elasticsearch.log
###ACTION_DELIMITER###
curl http://localhost:9200
###ACTION_DELIMITER###
pytest -v tests/
###ACTION_DELIMITER###
pip install datasets cleanlab
###ACTION_DELIMITER###
pytest -v tests/
###ACTION_DELIMITER###
pip install schedule
###ACTION_DELIMITER###
pytest -v tests/
###ACTION_DELIMITER###
pip install prodict
###ACTION_DELIMITER###
pytest -v tests/
###ACTION_DELIMITER###
pip install transformers
###ACTION_DELIMITER###
echo 'pytest -v tests/' > test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest -v tests/

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
pytest -v tests/

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
pytest -v tests/

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
RUN git clone https://github.com/argilla-io/argilla.git /home/argilla

WORKDIR /home/argilla
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("argilla-io", "argilla_v0_17_0")
class ARGILLA_V0_17_0(Instance):
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
        import json
        # Parse test cases using regex
        pattern = re.compile(r'^(tests/.*?)\s+(PASSED|FAILED|SKIPPED)\b', re.MULTILINE)
        for match in pattern.finditer(log):
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
