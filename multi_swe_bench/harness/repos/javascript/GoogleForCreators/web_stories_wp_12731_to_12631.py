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
        return "php:7.4-cli"
    
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
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs
###ACTION_DELIMITER###
curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
###ACTION_DELIMITER###
composer install
###ACTION_DELIMITER###
apt-get update && apt-get install -y unzip && docker-php-ext-install zip
###ACTION_DELIMITER###
apt-get update && apt-get install -y libzip-dev && docker-php-ext-install zip
###ACTION_DELIMITER###
composer install
###ACTION_DELIMITER###
ls vendor/ampproject/amp-wp/includes/bootstrap.php
###ACTION_DELIMITER###
composer install -v
###ACTION_DELIMITER###
sed -i 's|"ampproject/amp-wp/includes/bootstrap.php"|"includes/bootstrap.php"|' composer.json
###ACTION_DELIMITER###
sed -i '/ampproject\/amp-wp\/includes\/bootstrap.php/d' composer.json
###ACTION_DELIMITER###
composer install
###ACTION_DELIMITER###
sed -i 's|"exclude-from-files": \["includes/bootstrap.php"\]|"exclude-from-files": [{"package": "ampproject/amp-wp", "files": ["includes/bootstrap.php"]}]|' composer.json
###ACTION_DELIMITER###
sed -i '/"mcaskill\/composer-exclude-files": "^3.0",/d' composer.json && sed -i '/"exclude-from-files": \[.*\]/d' composer.json
###ACTION_DELIMITER###
composer install
###ACTION_DELIMITER###
rm -rf vendor && composer install
###ACTION_DELIMITER###
composer remove mcaskill/composer-exclude-files && composer install
###ACTION_DELIMITER###
npm install
###ACTION_DELIMITER###
cat .nvmrc
###ACTION_DELIMITER###
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
###ACTION_DELIMITER###
export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
###ACTION_DELIMITER###
nvm install 16 && nvm use 16
###ACTION_DELIMITER###
npm install
###ACTION_DELIMITER###
echo -e '#!/bin/bash
npm test -- --verbose
./vendor/bin/phpunit --verbose --testdox' > test_commands.sh
###ACTION_DELIMITER###
chmod +x test_commands.sh"""
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
#!/bin/bash
npm test -- --verbose
./vendor/bin/phpunit --verbose --testdox

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
npm test -- --verbose
./vendor/bin/phpunit --verbose --testdox

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
npm test -- --verbose
./vendor/bin/phpunit --verbose --testdox

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
FROM php:7.4-cli

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
RUN git clone https://github.com/GoogleForCreators/web-stories-wp.git /home/web-stories-wp

WORKDIR /home/web-stories-wp
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("GoogleForCreators", "web_stories_wp_12731_to_12631")
class WEB_STORIES_WP_12731_TO_12631(Instance):
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
        import json
        # Pattern to match passed tests (✔) and failed tests (✘)
        passed_pattern = re.compile(r'^\s+✔\s+(.*?)\s+\[\d+\.\d+\s+ms\]$', re.MULTILINE)
        failed_pattern = re.compile(r'^\s+✘\s+(.*?)\s+\[\d+\.\d+\s+ms\]$', re.MULTILINE)
        # Extract test names from log content
        passed_tests.update(passed_pattern.findall(log))
        failed_tests.update(failed_pattern.findall(log))
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
