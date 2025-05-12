# cat-all-files

`cat-all-files` is a powerful command-line utility that recursively prints, filters, and optionally copies the contents of all text files in a directory tree. It supports regex search, clipboard copy, extension filtering, skipping binaries, size limits, dry runs, and more.

## Features

- 📂 Recursively reads files in a directory
- 🧠 Skips binary files and hidden/system folders (e.g., `.git`, `node_modules`)
- 🔍 Supports search with plain text, regex, or whole-word match
- 📎 Optionally copies content to clipboard (per file or combined)
- 🔠 Filter files by extension
- 🚫 Skip large files or confirm interactively
- 🧪 Dry-run mode to preview which files will be read
- 📜 Logging support to write output to a file
- 🧾 Summary of files, size, and extension breakdown
- 🚀 Fast performance using `tqdm` for progress bars

## Installation

```bash
git clone https://github.com/BaseMax/cat-all-files.git
cd cat-all-files
pip install -r requirements.txt
```

## Usage

```bash
python cat_all_files.py [path] [options]
```

### Common Options

| Option               | Description |
|----------------------|-------------|
| `--copy`             | Copy each file's content to clipboard |
| `--combine`          | Copy all file contents into one clipboard entry |
| `--ext .py .txt`     | Only include files with specific extensions |
| `--max-size 1.0`     | Skip files larger than 1.0 MB |
| `--interactive-large`| Prompt before reading large files |
| `--search QUERY`     | Filter files containing QUERY |
| `--regex`            | Interpret search as a regular expression |
| `--whole-word`       | Match search as whole words only |
| `--no-hidden`        | Skip hidden files and directories |
| `--ignore build dist`| Additional folders/files to ignore |
| `--log output.txt`   | Write output to a file |
| `--dry-run`          | Print filenames only (no content read) |
| `--verbose`          | Print verbose logs |

### Example

```bash
python cat_all_files.py ./src --ext .py .md --search "TODO" --regex --combine --log output.txt
```

## Requirements

- Python 3.7+
- [colorama](https://pypi.org/project/colorama/)
- [pyperclip](https://pypi.org/project/pyperclip/)
- [tqdm](https://pypi.org/project/tqdm/)

Install dependencies with:

```bash
pip install -r requirements.txt
```

## License

MIT License

© 2025 Max Base  

See [LICENSE](LICENSE) for more information.
