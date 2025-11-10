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
apt-get install -y curl
###ACTION_DELIMITER###
curl -fsSL https://deb.nodesource.com/setup_14.x | bash -
###ACTION_DELIMITER###
curl -O https://nodejs.org/dist/v14.21.3/node-v14.21.3-linux-x64.tar.xz
###ACTION_DELIMITER###
tar -xJf node-v14.21.3-linux-x64.tar.xz
###ACTION_DELIMITER###
apt-get install -y xz-utils
###ACTION_DELIMITER###
tar -xJf node-v14.21.3-linux-x64.tar.xz
###ACTION_DELIMITER###
ln -s /home/sinopia_editor/node-v14.21.3-linux-x64/bin/node /usr/local/bin/node
###ACTION_DELIMITER###
ln -s /home/sinopia_editor/node-v14.21.3-linux-x64/bin/npm /usr/local/bin/npm
###ACTION_DELIMITER###
npm install
###ACTION_DELIMITER###
apt-get install -y python3 make g++
###ACTION_DELIMITER###
npm rebuild node-sass
###ACTION_DELIMITER###
npm install
###ACTION_DELIMITER###
npm cache clean --force && npm install
###ACTION_DELIMITER###
npm install --unsafe-perm
###ACTION_DELIMITER###
echo 'npm run test-verbose -- --verbose' > test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
npm run test-verbose -- --verbose

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
npm run test-verbose -- --verbose

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
npm run test-verbose -- --verbose

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
RUN git clone https://github.com/LD4P/sinopia_editor.git /home/sinopia_editor

WORKDIR /home/sinopia_editor
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("LD4P", "sinopia_editor_2554_to_2460")
class SINOPIA_EDITOR_2554_TO_2460(Instance):
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
        import re
        current_groups = []
        # Regex to strip ANSI escape codes
        ansi_escape = re.compile(r'\x1B\[[0-9;]*[mK]')
        # Regex to match test suite lines (captures path after status)
        suite_pattern = re.compile(r'^(PASS|FAIL|SKIPPED)\s+(.+?)\s*\(\d+\.\d+s\)$')
        # Regex patterns to match test cases (pass, fail) with duration
        pass_pattern = re.compile(r'^\s*✓\s+(.+?)\s*\(\d+ ms\)$')
        fail_pattern = re.compile(r'^\s*✕\s+(.+?)\s*\(\d+ ms\)$')
        # Regex to match nested test groups (e.g., "addProperty()")
        group_pattern = re.compile(r'^\s*([^\s✓✕○]+)\s*$')
        for line in log.split('\n'):
            # Strip ANSI escape codes
            clean_line = ansi_escape.sub('', line)
            # Check for test suite lines
            suite_match = suite_pattern.match(clean_line)
            if suite_match:
                # Extract suite name (e.g., resources.test.js)
                suite_path = suite_match.group(2)
                suite_name = suite_path.split('/')[-1]  # Get filename from path
                current_groups = [suite_name]
                continue
            # Check for passed tests
            pass_match = pass_pattern.match(clean_line)
            if pass_match:
                test_part = pass_match.group(1)
                # Remove duration (e.g., (5 ms))
                test_name = test_part.split('(')[0].strip()
                full_name = ' '.join(current_groups + [test_name])
                passed_tests.add(full_name)
                continue
            # Check for failed tests
            fail_match = fail_pattern.match(clean_line)
            if fail_match:
                test_part = fail_match.group(1)
                test_name = test_part.split('(')[0].strip()
                full_name = ' '.join(current_groups + [test_name])
                failed_tests.add(full_name)
                continue
            # Check if the line is a test group (indented, no symbol) and we're inside a test suite
            if not current_groups:
                continue  # Skip group processing if no test suite has been identified
            group_match = group_pattern.match(clean_line)
            if not group_match:
                continue
            stripped = group_match.group(1).strip()
            if not stripped:
                continue
            # Determine indentation level (assuming 2 spaces per level)
            indent = len(line) - len(line.lstrip())
            level = indent // 2
            # Update current_groups based on level
            # Truncate current_groups to the current level
            while len(current_groups) > level:
                current_groups.pop()
            # Ensure current_groups has exactly level elements by adding empty strings if necessary
            while len(current_groups) < level:
                current_groups.append("")
            # Add or update the current group
            group_name = stripped.rstrip(':').strip()
            if group_name:
                if len(current_groups) == level:
                    current_groups.append(group_name)
                else:
                    current_groups[level] = group_name
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
