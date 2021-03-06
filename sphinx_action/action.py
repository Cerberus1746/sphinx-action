import collections
import os
import shlex
import subprocess
import tempfile

from sphinx_action import status_check


GithubEnvironment = collections.namedtuple(
    "GithubEnvironment", ["build_command", "dependency_install_command"]
)


def extract_line_information(line_information):
    """
    Lines from sphinx log files look like this::

        /.../index.rst:22: WARNING: Problems with "include" directive path:
        InputError: [Errno 2] No such file or directory: 'I_DONT_EXIST'.

        /.../index.rst:22: WARNING: Problems with "include" directive path:
        InputError: [Errno 2] No such file or directory: 'I_DONT_EXIST'.

        /.../index.rst: Something went wrong with this whole file

    This method is responsible for parsing out the line number and file name from these lines.
    """
    line_num = -1
    file_and_line = line_information.split(":")

    # This is a dirty windows specific hack to deal with drive letters in the
    # start of the file-path, i.e D:\
    if len(file_and_line[0]) == 1:
        # If the first component is just one letter, we did an accidental split
        file_and_line[1] = file_and_line[0] + ":" + file_and_line[1]
        # Join the first component back up with the second and discard it.
        file_and_line = file_and_line[1:]

    if len(file_and_line) != 2 and len(file_and_line) != 3:
        return None

    # The case where we have no line number, in this case we return the line
    # number as 1 to mark the whole file.
    if len(file_and_line) == 2:
        line_num = 1

    if len(file_and_line) == 3:
        try:
            line_num = int(file_and_line[1])
        except ValueError:
            return None

    file_name = os.path.relpath(file_and_line[0])
    return file_name, line_num


def parse_sphinx_warnings_log(logs):
    """
    Parses a sphinx file containing warnings and errors into a list of
    status_check.CheckAnnotation objects.

    Inputs look like this::

        /.../warnings_and_errors/index.rst:19: WARNING: Error in "code-block" directive:
        maximum 1 argument(s) allowed, 2 supplied.

        /.../_setuptools_disclaimer.rst: WARNING: document isn't included in any toctree
        /.../contents.rst:5: WARNING: toctree contains reference to nonexisting document 'ayylmao'
    """
    annotations = []

    for i, line in enumerate(logs):
        if "WARNING" not in line:
            continue

        warning_tokens = line.split("WARNING:")
        if len(warning_tokens) != 2:
            continue

        file_and_line, message = warning_tokens

        file_and_line = extract_line_information(file_and_line)
        if not file_and_line:
            continue

        file_name, line_number = file_and_line

        warning_message = message
        # If this isn't the last line and the next line isn't a warning,
        # treat it as part of this warning message.
        if (i != len(logs) - 1) and "WARNING" not in logs[i + 1]:
            warning_message += logs[i + 1]

        warning_message = warning_message.strip()

        annotations.append(
            status_check.CheckAnnotation(
                path=file_name,
                message=warning_message,
                start_line=line_number,
                end_line=line_number,
                annotation_level=status_check.AnnotationLevel.WARNING,
            )
        )

    return annotations


def build_docs(github_env, docs_directory):
    build_command = github_env.build_command
    if not build_command:
        raise ValueError("Build command may not be empty")

    dependency_install_command = github_env.dependency_install_command
    if dependency_install_command:
        dependency_install_command = shlex.split(dependency_install_command)
        print(f"[sphinx-action] Running: {dependency_install_command}")
        subprocess.check_call(dependency_install_command)
    else:
        subprocess.check_call(["pip", "install", "-U", "Sphinx"])

    log_file = os.path.join(tempfile.gettempdir(), "sphinx-log")
    if os.path.exists(log_file):
        os.unlink(log_file)

    sphinx_options = f'--keep-going --no-color -w "{log_file}"'

    # If we're using make,
    # pass the options as part of the SPHINXOPTS environment variable,
    # otherwise pass them straight into the command.
    build_command = shlex.split(build_command)
    if build_command[0] == "make":
        # Pass the -e option into `make`,
        # this is specified to be Cause environment variables,
        # including those with null values,
        # to override macro assignments within makefiles.
        # Which is exactly what we want.
        build_command += ["-e"]
        print(f"[sphinx-action] Running: {build_command}")

        return_code = subprocess.call(
            build_command,
            env=dict(os.environ, SPHINXOPTS=sphinx_options),
            cwd=docs_directory,
        )
    else:
        build_command += shlex.split(sphinx_options)
        print(f"[sphinx-action] Running: {build_command}")

        return_code = subprocess.call(
            build_command + shlex.split(sphinx_options), cwd=docs_directory
        )

    with open(log_file, "r") as f:
        annotations = parse_sphinx_warnings_log(f.readlines())

    return return_code, annotations


def build_all_docs(github_env, docs_directories):
    if not any(docs_directories):
        raise ValueError("Please provide at least one docs directory to build")

    build_success = True
    warnings = 0

    for docs_dir in docs_directories:
        log_separator_title = f"Building docs in {docs_dir}"
        log_separator = "=" * len(log_separator_title)

        print(log_separator)
        print(log_separator_title)
        print(log_separator)

        return_code, annotations = build_docs(github_env, docs_dir)
        if return_code != 0:
            build_success = False

        warnings += len(annotations)

        for annotation in annotations:
            status_check.output_annotation(annotation)

    status_message = "[sphinx-action] Build {} with {} warnings".format(
        "succeeded" if build_success else "failed", warnings
    )
    print(status_message)

    if not build_success:
        raise RuntimeError("Build failed")
