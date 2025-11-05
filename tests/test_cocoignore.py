"""
Test script to verify .cocoignore file functionality

This script checks what files would be indexed by CocoIndex
with the current .cocoignore configuration.
"""

import os
import fnmatch
from pathlib import Path


def load_cocoignore_patterns():
    """Load patterns from .cocoignore file"""
    patterns = []
    try:
        with open('.cocoignore', 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    patterns.append(line)
        return patterns
    except FileNotFoundError:
        print("ERROR:  .cocoignore file not found")
        return []


def should_ignore_file(file_path, ignore_patterns):
    """Check if a file should be ignored based on .cocoignore patterns"""
    # Convert to relative path from project root and normalize path separators
    rel_path = str(file_path).replace('\\', '/')
    rel_path = rel_path.replace('//', '/')  # Remove double slashes

    for pattern in ignore_patterns:
        # Normalize pattern path separators
        normalized_pattern = pattern.replace('\\', '/')

        # Handle negation patterns (starting with !)
        if normalized_pattern.startswith('!'):
            # If file matches negation pattern, it should NOT be ignored
            neg_pattern = normalized_pattern[1:]
            if fnmatch.fnmatch(rel_path, neg_pattern):
                return False
            # Also check if any parent directory matches negation pattern
            if neg_pattern.endswith('/'):
                if any(fnmatch.fnmatch(part, neg_pattern.rstrip('/')) for part in rel_path.split('/')):
                    return False
        else:
            # Handle directory patterns (ending with /)
            if normalized_pattern.endswith('/'):
                if rel_path.startswith(normalized_pattern):
                    return True
            # Handle file patterns
            elif fnmatch.fnmatch(rel_path, normalized_pattern):
                return True
            # Handle glob patterns that might match subdirectories
            elif '*' in normalized_pattern:
                if fnmatch.fnmatch(rel_path, normalized_pattern):
                    return True

    return False


def scan_docs_directory():
    """Scan the docs directory and categorize files"""
    docs_path = Path("docs")
    if not docs_path.exists():
        print(" docs directory not found")
        return

    ignore_patterns = load_cocoignore_patterns()
    print(f"Loaded {len(ignore_patterns)} ignore patterns from .cocoignore")

    included_files = []
    excluded_files = []

    # Walk through all files in docs directory (same filter as main indexing function)
    supported_extensions = ['.md', '.rst', '.txt', '.py', '.js', '.html', '.css']

    for file_path in docs_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            rel_path = file_path.relative_to('.')

            if should_ignore_file(rel_path, ignore_patterns):
                excluded_files.append(rel_path)
            else:
                included_files.append(rel_path)

    # Print results
    print(f"\n Scan Results:")
    print(f"   Total files found: {len(included_files) + len(excluded_files)}")
    print(f"   Files to be indexed: {len(included_files)}")
    print(f"   Files excluded: {len(excluded_files)}")

    # Analyze file types
    print(f"\n Files to be Indexed (by type):")
    included_by_type = {}
    for file_path in included_files:
        suffix = file_path.suffix.lower()
        if suffix:
            included_by_type[suffix] = included_by_type.get(suffix, 0) + 1
        else:
            included_by_type['(no extension)'] = included_by_type.get('(no extension)', 0) + 1

    for ext, count in sorted(included_by_type.items()):
        print(f"   {ext}: {count} files")

    print(f"\n Files Excluded (by type):")
    excluded_by_type = {}
    for file_path in excluded_files:
        suffix = file_path.suffix.lower()
        if suffix:
            excluded_by_type[suffix] = excluded_by_type.get(suffix, 0) + 1
        else:
            excluded_by_type['(no extension)'] = excluded_by_type.get('(no extension)', 0) + 1

    for ext, count in sorted(excluded_by_type.items()):
        print(f"   {ext}: {count} files")

    # Show some examples
    print(f"\n Examples of files to be indexed:")
    for file_path in sorted(included_files)[:10]:
        print(f"   {file_path}")
    if len(included_files) > 10:
        print(f"   ... and {len(included_files) - 10} more")

    print(f"\n Examples of excluded files:")
    for file_path in sorted(excluded_files)[:10]:
        print(f"   {file_path}")
    if len(excluded_files) > 10:
        print(f"   ... and {len(excluded_files) - 10} more")

    # Check for potential issues
    print(f"\n Analysis:")

    # Check if we have documentation files
    doc_files = [f for f in included_files if f.suffix.lower() in ['.rst', '.md', '.txt']]
    print(f"   Documentation files (.rst, .md, .txt): {len(doc_files)}")

    if len(doc_files) == 0:
        print("     WARNING: No documentation files found!")
    elif len(doc_files) < 10:
        print("     WARNING: Very few documentation files found")
    else:
        print("    Good number of documentation files found")

    # Check for binary files that might have been missed
    binary_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf', '.exe', '.dll']
    binary_files = [f for f in included_files if f.suffix.lower() in binary_extensions]
    if binary_files:
        print(f"     WARNING: Found {len(binary_files)} binary files that should be excluded:")
        for file_path in binary_files[:5]:
            print(f"      {file_path}")
        if len(binary_files) > 5:
            print(f"      ... and {len(binary_files) - 5} more")
    else:
        print("    No binary files found in included files")

    return included_files, excluded_files


def test_consistency():
    """Test consistency between test and main indexing function"""
    print("\n Consistency Check:")
    print("-" * 30)

    try:
        # Import the main indexing function
        import sys
        sys.path.append('../src')
        from indexing.main_flow import load_cocoignore_patterns as main_load_patterns, should_ignore_file as main_should_ignore

        # Load patterns from both implementations
        test_patterns = load_cocoignore_patterns()
        main_patterns = main_load_patterns()

        print(f" Pattern loading: Test ({len(test_patterns)}) vs Main ({len(main_patterns)})")

        if test_patterns != main_patterns:
            print("  WARNING: Patterns differ between implementations!")
            print(f"   Test patterns: {test_patterns}")
            print(f"   Main patterns: {main_patterns}")
        else:
            print(" Patterns match between implementations")

        # Test with some sample files
        from pathlib import Path
        test_files = [
            Path('docs/godot-docs/.github/PULL_REQUEST_TEMPLATE.md'),
            Path('docs/godot-docs/_static/css/style.css'),
            Path('docs/godot-docs/about/introduction.rst'),
            Path('docs/godot-docs/404.rst'),
        ]

        all_match = True
        for test_file in test_files:
            if test_file.exists():
                test_result = should_ignore_file(test_file, test_patterns)
                main_result = main_should_ignore(test_file, main_patterns)

                status = "" if test_result == main_result else ""
                print(f"   {status} {test_file}: Test={test_result}, Main={main_result}")

                if test_result != main_result:
                    all_match = False

        if all_match:
            print(" All test files produce consistent results")
        else:
            print(" Inconsistencies found between implementations")

    except ImportError as e:
        print(f"  Could not import main indexing function: {e}")
        print("   This is expected if running from a different directory")


def main():
    """Main test function"""
    print("Testing .cocoignore Configuration")
    print("=" * 50)

    # Check if .cocoignore exists
    if not os.path.exists('.cocoignore'):
        print("ERROR:  .cocoignore file not found!")
        print("Make sure you're in the project root directory")
        return

    print("SUCCESS:  .cocoignore file found")

    # Scan and analyze
    included, excluded = scan_docs_directory()

    # Test consistency with main function
    test_consistency()

    print(f"\nSummary:")
    print(f"   The .cocoignore file will exclude {len(excluded)} files")
    print(f"   and allow indexing of {len(included)} documentation files.")
    print(f"   This should improve search quality and indexing performance.")

    print(f"\nNext Steps:")
    print(f"   1. Run the indexing function: uv run python -m src.indexing.main_flow")
    print(f"   2. Start the MCP server: uv run python -m src.mcp_server.server")


if __name__ == "__main__":
    main()