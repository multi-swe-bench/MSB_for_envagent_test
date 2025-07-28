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
                """ls
###ACTION_DELIMITER###
apt-get update && apt-get install -y software-properties-common
###ACTION_DELIMITER###
add-apt-repository -y ppa:deadsnakes/ppa
###ACTION_DELIMITER###
apt-get install -y python3.8 python3.8-venv python3.8-dev
###ACTION_DELIMITER###
python3.8 -m venv venv
###ACTION_DELIMITER###
source venv/bin/activate && pip install -r requirements.txt -r requirements_test.txt
###ACTION_DELIMITER###
cat << EOF > test_commands.sh
#!/bin/bash
source venv/bin/activate
python setup.py build_ext --inplace
nosetests -v --with-coverage --cover-erase --cover-min-percentage=100 --cover-package=zarr --with-doctest --doctest-options=+NORMALIZE_WHITESPACE zarr
python -m doctest -o NORMALIZE_WHITESPACE -o ELLIPSIS docs/tutorial.rst docs/spec/v2.rst
EOF && chmod +x test_commands.sh
###ACTION_DELIMITER###
echo '#!/bin/bash' > test_commands.sh && echo 'source venv/bin/activate' >> test_commands.sh && echo 'python setup.py build_ext --inplace' >> test_commands.sh && echo 'nosetests -v --with-coverage --cover-erase --cover-min-percentage=100 --cover-package=zarr --with-doctest --doctest-options=+NORMALIZE_WHITESPACE zarr' >> test_commands.sh && echo 'python -m doctest -o NORMALIZE_WHITESPACE -o ELLIPSIS docs/tutorial.rst docs/spec/v2.rst' >> test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
#!/bin/bash
source venv/bin/activate
python setup.py build_ext --inplace
nosetests -v --with-coverage --cover-erase --cover-min-percentage=100 --cover-package=zarr --with-doctest --doctest-options=+NORMALIZE_WHITESPACE zarr
python -m doctest -o NORMALIZE_WHITESPACE -o ELLIPSIS docs/tutorial.rst docs/spec/v2.rst

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
source venv/bin/activate
python setup.py build_ext --inplace
nosetests -v --with-coverage --cover-erase --cover-min-percentage=100 --cover-package=zarr --with-doctest --doctest-options=+NORMALIZE_WHITESPACE zarr
python -m doctest -o NORMALIZE_WHITESPACE -o ELLIPSIS docs/tutorial.rst docs/spec/v2.rst

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
source venv/bin/activate
python setup.py build_ext --inplace
nosetests -v --with-coverage --cover-erase --cover-min-percentage=100 --cover-package=zarr --with-doctest --doctest-options=+NORMALIZE_WHITESPACE zarr
python -m doctest -o NORMALIZE_WHITESPACE -o ELLIPSIS docs/tutorial.rst docs/spec/v2.rst

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
RUN git clone https://github.com/zarr-developers/zarr-python.git /home/zarr-python

WORKDIR /home/zarr-python
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("zarr-developers", "zarr-python_72_to_unknown")
class ZARR_PYTHON_72_TO_68(Instance):
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
        passed_tests = set[str]()  # Tests that passed successfully
        failed_tests = set[str]()  # Tests that failed
        skipped_tests = set[str]()  # Tests that were skipped
        import re
        # Parse test cases using regex patterns
        # Pattern for passed tests (ends with ' ... ok')
        passed_pattern = re.compile(r'^(.*?)\s+\.\.\.\s+ok$', re.MULTILINE)
        passed_tests = set(passed_pattern.findall(log))
        # Pattern for failed tests (starts with 'FAIL:' or 'ERROR:')
        failed_pattern = re.compile(r'^(FAIL|ERROR):\s+(.*)$', re.MULTILINE)
        failed_tests = set(m[1] for m in failed_pattern.findall(log) if m[1])
        # Pattern for skipped tests (ends with ' ... skipped' or starts with 'SKIPPED:')
        skipped_pattern = re.compile(r'^(.*?)\s+\.\.\.\s+skipped$|^SKIPPED:\s+(.*)$', re.MULTILINE)
        skipped_matches = skipped_pattern.findall(log)
        skipped_tests = set(m[0] if m[0] else m[1] for m in skipped_matches if m[0] or m[1])
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
