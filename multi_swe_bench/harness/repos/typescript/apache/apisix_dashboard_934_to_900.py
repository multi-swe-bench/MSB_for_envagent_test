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
        return "alpine:latest"
    
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
apk update
###ACTION_DELIMITER###
apk add --no-cache go nodejs yarn lua5.1
###ACTION_DELIMITER###
make build
###ACTION_DELIMITER###
apk add --no-cache make
###ACTION_DELIMITER###
make build
###ACTION_DELIMITER###
cd api && go mod download
###ACTION_DELIMITER###
ls -la conf
###ACTION_DELIMITER###
cat api/build.sh
###ACTION_DELIMITER###
echo -e '#!/bin/bash
set -e
cd api
go mod download
go build -o ../output/manager-api .
cp conf/schema.json ../output/conf/schema.json
mkdir -p ../output/dag-to-lua
if [ ! -f /tmp/dag-to-lua-1.1/lib/dag-to-lua.lua ]; then
  wget https://github.com/api7/dag-to-lua/archive/v1.1.tar.gz -P /tmp
  tar -zxvf /tmp/v1.1.tar.gz -C /tmp
fi
cp -r /tmp/dag-to-lua-1.1/lib/* ../output/dag-to-lua/
mkdir -p ../output/logs' > api/build.sh && chmod +x api/build.sh
###ACTION_DELIMITER###
echo -e '#!/bin/bash
set -e
go mod download
go build -o ../output/manager-api .
cp conf/schema.json ../output/conf/schema.json
mkdir -p ../output/dag-to-lua
if [ ! -f /tmp/dag-to-lua-1.1/lib/dag-to-lua.lua ]; then
  wget https://github.com/api7/dag-to-lua/archive/v1.1.tar.gz -P /tmp
  tar -zxvf /tmp/v1.1.tar.gz -C /tmp
fi
cp -r /tmp/dag-to-lua-1.1/lib/* ../output/dag-to-lua/
mkdir -p ../output/logs' > build.sh && chmod +x build.sh
###ACTION_DELIMITER###
cd .. && make build
###ACTION_DELIMITER###
echo -e '#!/bin/bash
set -e
cd api
go mod download
go build -o ../output/manager-api .
cp conf/schema.json ../output/conf/schema.json
mkdir -p ../output/dag-to-lua
if [ ! -f /tmp/dag-to-lua-1.1/lib/dag-to-lua.lua ]; then
  wget https://github.com/api7/dag-to-lua/archive/v1.1.tar.gz -P /tmp
  tar -zxvf /tmp/v1.1.tar.gz -C /tmp
fi
cp -r /tmp/dag-to-lua-1.1/lib/* ../output/dag-to-lua/
mkdir -p ../output/logs' > api/build.sh && chmod +x api/build.sh
###ACTION_DELIMITER###
make build
###ACTION_DELIMITER###
cd api && go mod tidy
###ACTION_DELIMITER###
cd api && go mod edit -replace github.com/coreos/bbolt=go.etcd.io/bbolt@v1.3.6 && go mod tidy
###ACTION_DELIMITER###
go mod edit -replace github.com/coreos/bbolt=go.etcd.io/bbolt@v1.3.6 && go mod tidy
###ACTION_DELIMITER###
cd .. && make build
###ACTION_DELIMITER###
apk update && apk add --no-cache ca-certificates && update-ca-certificates && cd web && yarn config set registry https://registry.npmjs.org/ && yarn install
###ACTION_DELIMITER###
apk update && apk add --no-cache ca-certificates && update-ca-certificates && yarn config set registry http://registry.npmjs.org/ && export NODE_TLS_REJECT_UNAUTHORIZED=0 && yarn install
###ACTION_DELIMITER###
date && apk add --no-cache --upgrade ca-certificates && update-ca-certificates && yarn config set registry https://registry.npmjs.org/ && yarn cache clean && export NODE_TLS_REJECT_UNAUTHORIZED=0 && yarn install
###ACTION_DELIMITER###
date -s '2024-09-16 03:36:47' && apk add --no-cache --upgrade ca-certificates && update-ca-certificates && yarn config set registry https://registry.npmjs.org/ && yarn cache clean && yarn install
###ACTION_DELIMITER###
ls -la web && cat web/.npmrc web/.yarnrc 2>/dev/null && sed -i 's/registry.npm.taobao.org/registry.npmjs.org/g' web/.npmrc web/.yarnrc package.json yarn.lock 2>/dev/null
###ACTION_DELIMITER###
ls -la
###ACTION_DELIMITER###
grep -r 'registry.npm.taobao.org' package.json yarn.lock && sed -i 's/registry.npm.taobao.org/registry.npmjs.org/g' package.json yarn.lock || echo 'No Taobao registry references found'
###ACTION_DELIMITER###
sed -i 's/registry.npm.taobao.org/registry.npmjs.org/g' yarn.lock && yarn install
###ACTION_DELIMITER###
rm -f yarn.lock && yarn config set registry https://registry.npmjs.org/ && yarn install
###ACTION_DELIMITER###
echo -e '#!/bin/bash
set -e
cd api && APISIX_API_WORKDIR=$PWD go test -v -race -cover -coverprofile=coverage.txt -covermode=atomic ./...
cd ../web && yarn test --verbose' > /home/apisix-dashboard/test_commands.sh && chmod +x /home/apisix-dashboard/test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
#!/bin/bash
set -e
cd api && APISIX_API_WORKDIR=$PWD go test -v -race -cover -coverprofile=coverage.txt -covermode=atomic ./...
cd ../web && yarn test --verbose

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
cd api && APISIX_API_WORKDIR=$PWD go test -v -race -cover -coverprofile=coverage.txt -covermode=atomic ./...
cd ../web && yarn test --verbose

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
cd api && APISIX_API_WORKDIR=$PWD go test -v -race -cover -coverprofile=coverage.txt -covermode=atomic ./...
cd ../web && yarn test --verbose

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
FROM alpine:latest

## Set noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install basic requirements
# For example: RUN apt-get update && apt-get install -y git
# For example: RUN yum install -y git
# For example: RUN apk add --no-cache git
RUN apk add --no-cache git

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


@Instance.register("apache", "apisix_dashboard_934_to_900")
class APISIX_DASHBOARD_934_TO_900(Instance):
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
        # Use regex to find test results
        result_pattern = re.compile(r"--- (PASS|FAIL|SKIPPED): (\w+) \(\d+\.\d+s\)")
        results = result_pattern.findall(log)
        for status, test_name in results:
            if status == "PASS":
                passed_tests.add(test_name)
            elif status == "FAIL":
                failed_tests.add(test_name)
            elif status == "SKIPPED":
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
