import os
import sys
import argparse
import re
from pathlib import Path
import pyperclip
from tqdm import tqdm

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
except ImportError:
    Fore = Style = type('', (), {'RESET_ALL': '', 'CYAN': '', 'RED': '', 'GREEN': '', 'YELLOW': '', 'MAGENTA': '', 'BLUE': ''})()

DEFAULT_IGNORES = {'node_modules', 'vendor', '.git', '__pycache__', '.DS_Store'}

summary = {
    "files_read": 0,
    "lines_read": 0,
    "bytes_read": 0,
    "extensions": {}
}

def human_readable_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"

def is_binary_file(path: Path, chunk_size: int = 1024) -> bool:
    try:
        with open(path, 'rb') as f:
            chunk = f.read(chunk_size)
            return b'\0' in chunk
    except Exception:
        return True

def should_ignore(path: Path, ignore_set: set, include_hidden: bool) -> bool:
    if not include_hidden and any(part.startswith('.') for part in path.parts if part != '.'):
        return True
    return any(part in ignore_set for part in path.parts)

def matches_search(content: str, search: str, regex: bool, whole_word: bool) -> bool:
    if regex:
        return re.search(search, content, re.IGNORECASE) is not None
    if whole_word:
        return re.search(rf'\b{re.escape(search)}\b', content, re.IGNORECASE) is not None
    return search.lower() in content.lower()

def print_file_contents(file_path: Path, *, copy_clipboard=False, verbose=False, max_size_mb=None,
                        search=None, regex=False, whole_word=False, combine=None, dry_run=False,
                        logger=None, interactive_large=False):
    try:
        size_bytes = file_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        if max_size_mb is not None and size_mb > max_size_mb:
            if interactive_large:
                confirm = input(f"{Fore.YELLOW}⚠ File {file_path} is {size_mb:.2f}MB. Read anyway? (y/n): {Style.RESET_ALL}")
                if confirm.lower() != 'y':
                    return
            else:
                if verbose:
                    print(f"{Fore.YELLOW}⚠ Skipping large file ({size_mb:.2f} MB): {file_path}{Style.RESET_ALL}")
                return

        if is_binary_file(file_path):
            if verbose:
                print(f"{Fore.MAGENTA}⚠ Skipping binary file: {file_path}{Style.RESET_ALL}")
            return

        if dry_run:
            print(f"{Fore.BLUE}📄 [Dry Run] Would read file: {file_path}{Style.RESET_ALL}")
            return

        with file_path.open('r', encoding='utf-8', errors='replace') as f:
            contents = f.read()
            if search and not matches_search(contents, search, regex, whole_word):
                return

            lines = contents.count('\n')
            summary["files_read"] += 1
            summary["lines_read"] += lines
            summary["bytes_read"] += size_bytes
            ext = file_path.suffix.lower() or '[no-ext]'
            summary["extensions"][ext] = summary["extensions"].get(ext, 0) + 1

            print(f"\n{Fore.CYAN}--- {file_path} ({lines} lines, {human_readable_size(size_bytes)}) ---{Style.RESET_ALL}")
            print(contents)

            if logger:
                logger.write(f"\n--- {file_path} ---\n{contents}\n")

            if copy_clipboard:
                pyperclip.copy(contents)
                print(f"{Fore.GREEN}✔ Copied to clipboard{Style.RESET_ALL}")

            if combine is not None:
                combine.append(contents)
    except Exception as e:
        print(f"{Fore.RED}✖ Failed to read {file_path}: {e}{Style.RESET_ALL}")

def traverse_and_read(directory: Path, *, ignore_set, copy_clipboard=False, only_exts=None, verbose=False,
                      max_size_mb=None, search=None, regex=False, whole_word=False,
                      include_hidden=True, dry_run=False, combine_all=False,
                      log_file=None, interactive_large=False):
    combined = [] if combine_all else None
    logger = open(log_file, 'w', encoding='utf-8') if log_file else None

    all_files = []
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d, ignore_set, include_hidden)]
        for file in files:
            file_path = Path(root) / file
            if should_ignore(file_path, ignore_set, include_hidden):
                continue
            if only_exts and file_path.suffix.lower() not in only_exts:
                continue
            all_files.append(file_path)

    for file_path in tqdm(all_files, desc="Processing files"):
        print_file_contents(
            file_path,
            copy_clipboard=copy_clipboard,
            verbose=verbose,
            max_size_mb=max_size_mb,
            search=search,
            regex=regex,
            whole_word=whole_word,
            combine=combined,
            dry_run=dry_run,
            logger=logger,
            interactive_large=interactive_large
        )

    if combine_all and combined:
        combined_output = "\n\n".join(combined)
        pyperclip.copy(combined_output)
        print(f"{Fore.GREEN}✔ Combined output copied to clipboard ({len(combined)} files){Style.RESET_ALL}")

    if logger:
        logger.close()

def print_summary():
    print(f"\n{Fore.GREEN}✅ Done.")
    print(f"{Fore.GREEN}Files read: {summary['files_read']}")
    print(f"{Fore.GREEN}Lines: {summary['lines_read']}")
    print(f"{Fore.GREEN}Size: {human_readable_size(summary['bytes_read'])}")
    print(f"{Fore.GREEN}Extension breakdown:")
    for ext, count in sorted(summary["extensions"].items(), key=lambda x: x[0]):
        print(f"{Fore.GREEN}  {ext}: {count} file(s){Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description="📂 Recursively print, filter, and optionally copy file contents.")
    parser.add_argument("path", nargs="?", default=os.getcwd(), help="Directory to scan.")
    parser.add_argument("--ignore", nargs="*", default=[], help="Dirs/files to ignore.")
    parser.add_argument("--copy", action="store_true", help="Copy each file's contents to clipboard.")
    parser.add_argument("--combine", action="store_true", help="Copy all contents into one clipboard entry.")
    parser.add_argument("--ext", nargs="*", default=[], help="Only include files with these extensions.")
    parser.add_argument("--verbose", action="store_true", help="Verbose mode.")
    parser.add_argument("--max-size", type=float, help="Skip files larger than this size (MB).")
    parser.add_argument("--interactive-large", action="store_true", help="Prompt before reading large files.")
    parser.add_argument("--search", type=str, help="Search for this string inside files.")
    parser.add_argument("--regex", action="store_true", help="Interpret --search as regex.")
    parser.add_argument("--whole-word", action="store_true", help="Match whole words for --search.")
    parser.add_argument("--no-hidden", action="store_true", help="Ignore hidden files/folders.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate the run without reading files.")
    parser.add_argument("--log", type=str, help="Log output to specified file.")
    args = parser.parse_args()

    ignore_set = DEFAULT_IGNORES.union(set(args.ignore))
    only_exts = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in args.ext}

    directory = Path(args.path).resolve()
    if not directory.is_dir():
        print(f"{Fore.RED}✖ Error: {directory} is not a valid directory.{Style.RESET_ALL}")
        sys.exit(1)

    print(f"{Fore.GREEN}📁 Scanning: {directory}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}🚫 Ignoring: {sorted(ignore_set)}{Style.RESET_ALL}")
    if only_exts:
        print(f"{Fore.BLUE}📄 Extensions filter: {sorted(only_exts)}{Style.RESET_ALL}")
    if args.max_size:
        print(f"{Fore.YELLOW}⛔ Max file size: {args.max_size} MB{Style.RESET_ALL}")
    if args.search:
        print(f"{Fore.CYAN}🔍 Searching for: \"{args.search}\" (regex={args.regex}, whole_word={args.whole_word}){Style.RESET_ALL}")
    if args.dry_run:
        print(f"{Fore.BLUE}🧪 Dry run mode enabled (no file reads){Style.RESET_ALL}")

    try:
        traverse_and_read(
            directory=directory,
            ignore_set=ignore_set,
            copy_clipboard=args.copy and not args.combine,
            only_exts=only_exts,
            verbose=args.verbose,
            max_size_mb=args.max_size,
            search=args.search,
            regex=args.regex,
            whole_word=args.whole_word,
            include_hidden=not args.no_hidden,
            dry_run=args.dry_run,
            combine_all=args.combine,
            log_file=args.log,
            interactive_large=args.interactive_large
        )
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}✋ Interrupted by user.{Style.RESET_ALL}")
        sys.exit(1)

    print_summary()

if __name__ == "__main__":
    main()
