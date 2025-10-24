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
        return "ubuntu:22.04"
    
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
apt-get update
###ACTION_DELIMITER###
apt-get install -y golang nodejs etcd
###ACTION_DELIMITER###
npm install -g yarn
###ACTION_DELIMITER###
apt-get install -y npm
###ACTION_DELIMITER###
npm install -g yarn
###ACTION_DELIMITER###
make build
###ACTION_DELIMITER###
apt-get install -y wget
###ACTION_DELIMITER###
make build
###ACTION_DELIMITER###
apt-get update && apt-get install --reinstall -y ca-certificates
###ACTION_DELIMITER###
make build
###ACTION_DELIMITER###
cd web && export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true && NODE_TLS_REJECT_UNAUTHORIZED=0 yarn install
###ACTION_DELIMITER###
npm config set registry https://registry.npmjs.org/ && yarn config set strict-ssl false && export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true && NODE_TLS_REJECT_UNAUTHORIZED=0 yarn install
###ACTION_DELIMITER###
yarn build
###ACTION_DELIMITER###
echo -e '#!/bin/bash
cd api && APISIX_API_WORKDIR=$(pwd) go test -v -count=1 -race -cover -coverprofile=coverage.txt -covermode=atomic -json ./...' > /home/apisix-dashboard/test_commands.sh && chmod +x /home/apisix-dashboard/test_commands.sh
###ACTION_DELIMITER###
cat package.json
###ACTION_DELIMITER###
echo -e '#!/bin/bash
set -e
# Run API tests
cd /home/apisix-dashboard/api && APISIX_API_WORKDIR=$(pwd) go test -v -count=1 -race -cover -coverprofile=coverage.txt -covermode=atomic -json ./...
# Run web component tests
cd /home/apisix-dashboard/web && yarn test:component --verbose
# Run web E2E tests
yarn test:e2e --verbose' > /home/apisix-dashboard/test_commands.sh && chmod +x /home/apisix-dashboard/test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
#!/bin/bash
set -e
# Run API tests
cd /home/apisix-dashboard/api && APISIX_API_WORKDIR=$(pwd) go test -v -count=1 -race -cover -coverprofile=coverage.txt -covermode=atomic -json ./...
# Run web component tests
cd /home/apisix-dashboard/web && yarn test:component --verbose
# Run web E2E tests
yarn test:e2e --verbose

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
#!/bin/bash
set -e
# Run API tests
cd /home/apisix-dashboard/api && APISIX_API_WORKDIR=$(pwd) go test -v -count=1 -race -cover -coverprofile=coverage.txt -covermode=atomic -json ./...
# Run web component tests
cd /home/apisix-dashboard/web && yarn test:component --verbose
# Run web E2E tests
yarn test:e2e --verbose

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
#!/bin/bash
set -e
# Run API tests
cd /home/apisix-dashboard/api && APISIX_API_WORKDIR=$(pwd) go test -v -count=1 -race -cover -coverprofile=coverage.txt -covermode=atomic -json ./...
# Run web component tests
cd /home/apisix-dashboard/web && yarn test:component --verbose
# Run web E2E tests
yarn test:e2e --verbose

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

# Choose an appropriate base image based on the project's requirements - replace [base image] with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM ubuntu:22.04

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
RUN git clone https://github.com/apache/apisix-dashboard.git /home/apisix-dashboard

WORKDIR /home/apisix-dashboard
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("apache", "apisix_dashboard_1111_to_977")
class APISIX_DASHBOARD_1111_TO_977(Instance):
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
        import json
        # Parse each line of the log
        for line in log.splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue  # Skip invalid JSON lines
            test_name = entry.get("Test")
            if not test_name:
                continue  # Skip entries without a test name
            action = entry.get("Action")
            if action == "pass":
                passed_tests.add(test_name)
            elif action == "fail":
                failed_tests.add(test_name)
            elif action == "skip":
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
