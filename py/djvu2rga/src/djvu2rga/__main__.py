import re
import subprocess
import sys

PAGE_PATTERN: re.Pattern[str] = re.compile(r'^\s*(\d+)\s+[AIPT]+')


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} FILE_PATH")
        exit()
    input_file: str = sys.argv[1]
    file_to_page: list[int | None] = []
    for file_info in subprocess.run(
            ['djvused', input_file, '-e', 'ls'],
            capture_output=True,
            text=True
            ).stdout.splitlines():
        m: re.Match[str] | None = PAGE_PATTERN.match(file_info)
        file_to_page.append(None if m is None else int(m.group(1)))
    file_to_page.append(None)  # print-pure-txt add \x0c to the end
    file: int = 0
    for file_text in subprocess.run(
            ['djvused', input_file, '-e', 'print-pure-txt'],
            capture_output=True
            ).stdout.split(b'\x0c'):
        if file_to_page[file] is not None:
            sys.stdout.buffer.write(file_text + b'\x0c')
        file += 1

if __name__ == '__main__':
    main()

