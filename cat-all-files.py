import os
import argparse
from pathlib import Path
import pyperclip
import sys

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
except ImportError:
    Fore = Style = type('', (), {'RESET_ALL': '', 'CYAN': '', 'RED': '', 'GREEN': '', 'YELLOW': ''})()

DEFAULT_IGNORES = {
    'node_modules',
    'vendor',
    '.git',
    '__pycache__',
    '.DS_Store'
}

def should_ignore(path: Path, ignore_set: set) -> bool:
    return any(part in ignore_set for part in path.parts)

def print_file_contents(file_path: Path, copy_clipboard: bool = False, verbose: bool = False, max_size_mb: float = None):
    try:
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if max_size_mb is not None and size_mb > max_size_mb:
            if verbose:
                print(f"{Fore.YELLOW}Skipping large file ({size_mb:.2f} MB): {file_path}{Style.RESET_ALL}")
            return

        with file_path.open('r', encoding='utf-8', errors='replace') as f:
            contents = f.read()
            lines = contents.count('\n')
            print(f"\n{Fore.CYAN}--- {file_path} ({lines} lines) ---{Style.RESET_ALL}")
            print(contents)
            if copy_clipboard:
                pyperclip.copy(contents)
                print(f"{Fore.GREEN}✔ Copied to clipboard{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}✖ Failed to read {file_path}: {e}{Style.RESET_ALL}")

def traverse_and_read(directory: Path, ignore_set: set, copy_clipboard: bool = False,
                      only_exts: set = None, verbose: bool = False, max_size_mb: float = None):
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d, ignore_set)]
        for file in files:
            file_path = Path(root) / file
            if should_ignore(file_path, ignore_set):
                continue
            if only_exts and file_path.suffix.lower() not in only_exts:
                continue
            print(f"\n{Fore.YELLOW}Found File: {file_path}{Style.RESET_ALL}")
            print_file_contents(file_path, copy_clipboard=copy_clipboard, verbose=verbose, max_size_mb=max_size_mb)

def main():
    parser = argparse.ArgumentParser(description="Recursively print and optionally copy file contents from a directory.")
    parser.add_argument(
        "path", nargs="?", default=os.getcwd(),
        help="Path to the directory (default: current directory)."
    )
    parser.add_argument(
        "--ignore", nargs="*", default=[],
        help="Extra dirs/files to ignore (space-separated)."
    )
    parser.add_argument(
        "--copy", action="store_true",
        help="Copy file contents to clipboard after reading."
    )
    parser.add_argument(
        "--ext", nargs="*", default=[],
        help="Only include files with these extensions (e.g. .py .txt)."
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose output."
    )
    parser.add_argument(
        "--max-size", type=float, default=None,
        help="Skip files larger than this size (in MB)."
    )
    args = parser.parse_args()

    ignore_set = DEFAULT_IGNORES.union(set(args.ignore))
    only_exts = set(ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in args.ext)

    directory = Path(args.path).resolve()
    if not directory.is_dir():
        print(f"{Fore.RED}✖ Error: {directory} is not a valid directory.{Style.RESET_ALL}")
        sys.exit(1)

    print(f"{Fore.GREEN}📁 Scanning: {directory}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}🚫 Ignoring: {sorted(ignore_set)}{Style.RESET_ALL}")
    if only_exts:
        print(f"{Fore.BLUE}📄 Filtering by extensions: {sorted(only_exts)}{Style.RESET_ALL}")
    if args.max_size:
        print(f"{Fore.BLUE}⛔ Skipping files > {args.max_size} MB{Style.RESET_ALL}")

    try:
        traverse_and_read(directory, ignore_set, copy_clipboard=args.copy,
                          only_exts=only_exts, verbose=args.verbose, max_size_mb=args.max_size)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}✋ Interrupted by user.{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
