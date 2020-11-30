#!/usr/bin/env python3
import os
from sphinx_action import action

# This is the entrypoint called by Github when our action is run. All the
# Github specific setup is done here to make it easy to test the action code
# in isolation.
if __name__ == "__main__":
    print("[sphinx-action] Starting sphinx-action build.")

    build_command = os.environ.get("INPUT_BUILD-COMMAND")
    docs_build = os.environ.get("INPUT_DOCS-FOLDER")
    pre_build_command = os.environ.get("INPUT_PRE-BUILD-COMMAND")

    if pre_build_command:
        print(f"Running: {pre_build_command}")
        os.system(pre_build_command)

    github_env = action.GithubEnvironment(
        build_command=os.environ.get("INPUT_BUILD-COMMAND"),
        dependency_install_command=os.environ.get(
            "INPUT_DEPENDENCY-INSTALL-COMMAND"
        )
    )

    # We build the doc folder passed in the inputs.
    action.build_all_docs(github_env, [docs_build if docs_build else "docs/"])
