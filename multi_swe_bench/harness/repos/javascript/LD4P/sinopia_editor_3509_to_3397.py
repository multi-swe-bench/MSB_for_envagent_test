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
apt-get install -y curl
###ACTION_DELIMITER###
curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
###ACTION_DELIMITER###
apt-get install nodejs -y
###ACTION_DELIMITER###
npm install
###ACTION_DELIMITER###
echo 'NODE_OPTIONS=--max-old-space-size=8192 ./node_modules/jest/bin/jest.js --verbose --runInBand --colors' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e 'export NODE_OPTIONS=--max-old-space-size=12288
./node_modules/jest/bin/jest.js --verbose --runInBand --colors' > test_commands.sh
###ACTION_DELIMITER###
chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e 'export NODE_OPTIONS=--max-old-space-size=16384
export AMPLIFY_CONFIG={"auth":{"region":"us-east-1","userPoolId":"mock","userPoolWebClientId":"mock"}}
npm run test-verbose' > test_commands.sh
###ACTION_DELIMITER###
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
###ACTION_DELIMITER###
apt-get install nodejs -y
###ACTION_DELIMITER###
rm -rf node_modules package-lock.json && npm install
###ACTION_DELIMITER###
echo -e 'export NODE_OPTIONS=--max-old-space-size=16384
export AMPLIFY_CONFIG={"auth":{"region":"us-east-1","userPoolId":"mock","userPoolWebClientId":"mock"}}
npm run test-verbose' > test_commands.sh
###ACTION_DELIMITER###
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
###ACTION_DELIMITER###
apt-get install nodejs -y
###ACTION_DELIMITER###
echo -e 'echo "window._amplifyConfig = {\n  Auth: {\n    region: \"us-east-1\",\n    userPoolId: \"mock\",\n    userPoolWebClientId: \"mock\"\n  }\n};" > src/aws-exports.js\nexport NODE_OPTIONS=--max-old-space-size=24576\nnpm run test-verbose' > test_commands.sh
###ACTION_DELIMITER###
chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
npm install jest@latest @types/jest@latest ts-jest@latest jest-environment-jsdom@latest --save-dev
###ACTION_DELIMITER###
npm install jest@latest babel-jest@^29.0.0 ts-jest@latest @types/jest@latest jest-environment-jsdom@latest --save-dev --legacy-peer-deps
###ACTION_DELIMITER###
echo 'module.exports = { testEnvironment: "jsdom", setupFilesAfterEnv: ["./react-testing-library.setup.js"] }' > jest.config.js
###ACTION_DELIMITER###
npx jest --clearCache
###ACTION_DELIMITER###
echo -e 'export NODE_OPTIONS=--max-old-space-size=24576
npm run test-verbose -- --config jest.config.js' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo 'module.exports = { testEnvironment: "jsdom", transform: { "^.+\\.(js|jsx)$": "babel-jest" }, transformIgnorePatterns: ["node_modules/(?!(nanoid)/)"] }' > jest.config.js
###ACTION_DELIMITER###
npx jest --clearCache --config jest.config.js
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###

###ACTION_DELIMITER###
npm install @testing-library/jest-dom --save-dev
###ACTION_DELIMITER###
echo 'import "@testing-library/jest-dom";' > react-testing-library.setup.js
###ACTION_DELIMITER###
echo 'module.exports = { testEnvironment: "jsdom", transform: { "^.+\\.(js|jsx)$": "babel-jest" }, transformIgnorePatterns: ["node_modules/(?!(nanoid)/)"], setupFilesAfterEnv: ["./react-testing-library.setup.js"] }' > jest.config.js
###ACTION_DELIMITER###
sed -i 's/"@babel\/preset-env"/"@babel\/preset-env", { "modules": "commonjs" }/' .babelrc
###ACTION_DELIMITER###

###ACTION_DELIMITER###
cat .babelrc
###ACTION_DELIMITER###
npx jest --clearCache --config jest.config.js && bash test_commands.sh
###ACTION_DELIMITER###
sed -i 's/"presets": \["@babel\\/preset-env", { "modules": "commonjs" }, "@babel\\/preset-react"\]/"presets": [["@babel\\/preset-env", { "modules": "commonjs" }], "@babel\\/preset-react"]/' .babelrc
###ACTION_DELIMITER###
sed -i 's|"presets": \["@babel/preset-env", { "modules": "commonjs" }, "@babel/preset-react"\]|"presets": \[["@babel/preset-env", { "modules": "commonjs" }], "@babel/preset-react"\]|g' .babelrc
###ACTION_DELIMITER###
cat .babelrc
###ACTION_DELIMITER###
npx jest --clearCache --config jest.config.js && bash test_commands.sh
###ACTION_DELIMITER###

###ACTION_DELIMITER###
sed -i 's/"modules": "commonjs"/"modules": "commonjs", "targets": { "node": "current" }/' .babelrc
###ACTION_DELIMITER###
"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
export NODE_OPTIONS=--max-old-space-size=24576
npm run test-verbose -- --config jest.config.js

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
export NODE_OPTIONS=--max-old-space-size=24576
npm run test-verbose -- --config jest.config.js

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
export NODE_OPTIONS=--max-old-space-size=24576
npm run test-verbose -- --config jest.config.js

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

# Choose an appropriate base image based on the project's requirements - replace ubuntu:22.04 with actual base image
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
RUN git clone https://github.com/LD4P/sinopia_editor.git /home/sinopia_editor

WORKDIR /home/sinopia_editor
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("LD4P", "sinopia_editor_3509_to_3397")
class SINOPIA_EDITOR_3509_TO_3397(Instance):
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
        # Remove ANSI escape codes (e.g., \x1b[32m)
        clean_log = re.sub(r'\x1b\[[0-9;]*m', '', log)
        # Match PASS/FAIL/SKIPPED statuses and extract test names
        pattern = re.compile(r'(PASS|FAIL|SKIPPED)\s+(.+?\.test\.js)')
        for line in clean_log.split('\n'):
            match = pattern.search(line.strip())
            if match:
                status, test_name = match.groups()
                test_name = test_name.strip()
                if status == 'PASS':
                    passed_tests.add(test_name)
                elif status == 'FAIL':
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
