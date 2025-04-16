import os
import pty
import signal
import subprocess
import time
from glob import glob


def main():
    # cd c; RUNDOCKER=true python3 ../run_all_examples.py
    if os.getenv("RUNDOCKER"):
        with open("README.md", "r") as file:
            subprocess.Popen(
                _extract_docker_cmd(file.read().splitlines()),
                shell=True,
            ).wait()
        return

    example_timeout = int(os.getenv("TIMEOUT") or "30")

    filter_langs_str = os.getenv("FILTERLANG")
    filter_langs = filter_langs_str.split(",") if filter_langs_str else None

    filter_sections_str = os.getenv("FILTERSECTION")
    filter_sections = filter_sections_str.split(",") if filter_sections_str else None

    filter_examples_str = os.getenv("FILTEREXAMPLE")
    filter_examples = filter_examples_str.split(",") if filter_examples_str else None

    root = os.path.abspath(os.getcwd())

    for readme_path in sorted(glob("*/README.md")):
        language = readme_path.split("/")[0]

        if filter_langs and language not in filter_langs:
            continue

        language_path = os.path.join(root, language)
        readme_path = os.path.join(root, readme_path)

        with open(readme_path, "r") as file:
            readme_lines = file.read().splitlines()

        print(f"# Language: {language}")
        print()

        os.chdir(language_path)

        docker_cmd = _extract_docker_cmd(readme_lines)

        for example in _extract_all_examples(readme_lines):
            if filter_sections and example["section"] not in filter_sections:
                continue

            if filter_examples and example["name"] not in filter_examples:
                continue

            print(f"Example: {example['section']} / {example['name']}")

            _run_example(docker_cmd, example["cmd"], example_timeout)

            print()
            print("##########")
            print()

        print()
        print("==============================")
        print()


def _run_example(docker_cmd: str, example_cmd: str, timeout: int):
    example_cmd = example_cmd.replace("\n", " && ")

    docker_cmd = docker_cmd.strip()

    if docker_cmd.endswith("exec sh'"):
        docker_cmd = docker_cmd.replace("exec sh'", f"set -e; {example_cmd}'")
    elif docker_cmd.endswith("exec bash'"):
        docker_cmd = docker_cmd.replace("exec bash'", f"set -e; {example_cmd}'")
    else:
        docker_cmd += f" sh -c 'set -e; {example_cmd}'"

    if os.getenv("DRYRUN"):
        print(docker_cmd)
        return

    docker_process = subprocess.Popen(
        docker_cmd,
        shell=True,
        preexec_fn=os.setsid,
    )

    _wait_timeout(docker_process, timeout)


def _extract_all_examples(readme_lines: list[str]):
    examples = []
    examples.extend(_extract_examples(readme_lines, "Async (REST API)"))
    examples.extend(_extract_examples(readme_lines, "Real-time (WebSocket API)"))
    return examples


def _extract_examples(readme_lines: list[str], section: str):
    in_section = False
    in_example = False
    in_code_block = False
    example_name = ""
    example_cmd_lines = []
    examples = []

    for line in readme_lines:
        if line == f"## {section}":
            in_section = True
        elif in_section and line.startswith("## "):
            break
        elif in_section and line.startswith("### "):
            in_example = True
            example_name = line[4:]
        elif in_example and line == "```sh":
            in_code_block = True
        elif in_code_block and line == "```":
            examples.append(
                {
                    "section": section,
                    "name": example_name,
                    "cmd": "\n".join(example_cmd_lines),
                }
            )
            in_code_block = False
            example_cmd_lines = []
        elif in_code_block:
            example_cmd_lines.append(line)

    return examples


def _extract_docker_cmd(readme_lines: list[str]):
    in_docker_section = False
    in_code_block = False
    cmd_lines = []

    for line in readme_lines:
        if line == "## Run with Docker":
            in_docker_section = True
        elif in_docker_section and line == "```sh":
            in_code_block = True
        elif in_code_block and line == "```":
            in_code_block = False
        elif in_code_block:
            cmd_lines.append(line)
    return "\n".join(cmd_lines)


def _wait_timeout(proc: subprocess.Popen, seconds: int):
    start = time.time()
    end = start + seconds

    while True:
        code = proc.poll()
        if code is not None:
            assert code == 0
            return
        if time.time() >= end:
            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
            return
        time.sleep(0.5)


if __name__ == "__main__":
    main()
