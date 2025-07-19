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
pip install -r requirements.txt
###ACTION_DELIMITER###
echo 'python -c "import skimage, sys, io; sys.exit(skimage.test_verbose())"' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
python setup.py build_ext -i
###ACTION_DELIMITER###
pip uninstall -y cython && pip install 'cython<3.0'
###ACTION_DELIMITER###
python setup.py build_ext -i
###ACTION_DELIMITER###
pip uninstall -y numpy && pip install 'numpy<2.0'
###ACTION_DELIMITER###
python setup.py build_ext -i
###ACTION_DELIMITER###
pip uninstall -y setuptools && pip install 'setuptools<60.0'
###ACTION_DELIMITER###
python setup.py build_ext -i
###ACTION_DELIMITER###
apt-get update && apt-get install -y gcc
###ACTION_DELIMITER###
python setup.py build_ext -i
###ACTION_DELIMITER###
cython skimage/restoration/_nl_means_denoising.pyx
###ACTION_DELIMITER###
python setup.py build_ext -i
###ACTION_DELIMITER###
cython skimage/measure/_ccomp.pyx
###ACTION_DELIMITER###
sed -i 's/DTYPE = cnp.intp/ctypedef cnp.intp DTYPE/' skimage/measure/_ccomp.pxd
###ACTION_DELIMITER###
sed -i 's/cnp.intp/cnp.npy_intp/' skimage/measure/_ccomp.pxd
###ACTION_DELIMITER###
cython skimage/measure/_ccomp.pyx
###ACTION_DELIMITER###
sed -i 's/npy_intp_t/npy_intp/' skimage/measure/_ccomp.pxd
###ACTION_DELIMITER###
sed -i '/DTYPE = np.intp/d' skimage/measure/_ccomp.pyx
###ACTION_DELIMITER###
cython skimage/measure/_ccomp.pyx
###ACTION_DELIMITER###
sed -i 's/astype(DTYPE)/astype(np.intp)/' skimage/measure/_ccomp.pyx
###ACTION_DELIMITER###
cython skimage/measure/_ccomp.pyx
###ACTION_DELIMITER###
sed -i 's/dtype=DTYPE/dtype=np.intp/' skimage/measure/_ccomp.pyx
###ACTION_DELIMITER###
sed -i 's/dtype=DTYPE/dtype=np.intp/' skimage/measure/_ccomp.pyx
###ACTION_DELIMITER###
sed -i 's/dtype[[:space:]]*=[[:space:]]*DTYPE/dtype=np.intp/' skimage/measure/_ccomp.pyx
###ACTION_DELIMITER###
cython skimage/measure/_ccomp.pyx
###ACTION_DELIMITER###
python setup.py build_ext -i
###ACTION_DELIMITER###
cython skimage/segmentation/_felzenszwalb_cy.pyx
###ACTION_DELIMITER###
python setup.py build_ext -i
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install nose
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip uninstall -y numpy && pip install 'numpy==1.19.5'
###ACTION_DELIMITER###
pip uninstall -y numpy && pip install 'numpy==1.23.5'
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e 'export PYTHONWARNINGS=ignore::DeprecationWarning
nosetests skimage -v' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e 'export PYTHONWARNINGS=ignore::DeprecationWarning
python -c "import skimage, sys; sys.exit(skimage.test_verbose())"' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
export PYTHONWARNINGS=ignore::DeprecationWarning
python -c "import skimage, sys; sys.exit(skimage.test_verbose())"

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
export PYTHONWARNINGS=ignore::DeprecationWarning
python -c "import skimage, sys; sys.exit(skimage.test_verbose())"

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
export PYTHONWARNINGS=ignore::DeprecationWarning
python -c "import skimage, sys; sys.exit(skimage.test_verbose())"

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
RUN git clone https://github.com/scikit-image/scikit-image.git /home/scikit-image

WORKDIR /home/scikit-image
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("scikit-image", "scikit-image_v0_11_0")
class SCIKIT_IMAGE_V0_11_0(Instance):
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
        statuses = {'ok', 'FAIL', 'skipped'}
        current_test = None
        for line in log.split('\n'):
            line = line.rstrip('\n')
            if current_test is None:
                if ' ... ' in line:
                    test_part, rest_part = line.split(' ... ', 1)
                    test_name = test_part.strip()
                    rest_stripped = rest_part.strip()
                    if rest_stripped in statuses:
                        # Status is on the same line
                        if rest_stripped == 'ok':
                            passed_tests.add(test_name)
                        elif rest_stripped == 'FAIL':
                            failed_tests.add(test_name)
                        elif rest_stripped == 'skipped':
                            skipped_tests.add(test_name)
                    else:
                        current_test = test_name
            else:
                line_stripped = line.strip()
                if line_stripped in statuses:
                    if line_stripped == 'ok':
                        passed_tests.add(current_test)
                    elif line_stripped == 'FAIL':
                        failed_tests.add(current_test)
                    elif line_stripped == 'skipped':
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
