import os
import pathspec
import glob

def load_gitignore_for_directory(path):
    gitignore_files = []
    current_path = os.path.abspath(path)

    # First, collect all gitignore paths from root to leaf
    while True:
        gitignore_path = os.path.join(current_path, '.gitignore')
        if os.path.exists(gitignore_path):
            gitignore_files.append(gitignore_path)
        parent_path = os.path.dirname(current_path)
        if current_path == parent_path:
            break
        current_path = parent_path
    
    # Reverse to process from root to leaf (so leaf patterns can override root patterns)
    gitignore_files.reverse()
    
    # Now read patterns from all files
    patterns = []
    for gitignore_path in gitignore_files:
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)

    # Create a single PathSpec from all collected patterns
    return pathspec.PathSpec.from_lines('gitwildmatch', patterns) if patterns else None

# Check if file or directory is ignored with pre-loaded specs
def is_ignored(path, base_path, spec):
    relative_path = os.path.relpath(path, base_path)
    # Consider it a directory if it ends with '/' or if it exists and is a directory
    is_dir = path.endswith('/') or os.path.isdir(path)
    if is_dir and not relative_path.endswith('/'):
        relative_path += '/'
    return spec.match_file(relative_path) if spec else False


# Custom tool: read current directory structure honoring .gitignore correctly
def read_directory_structure(path, work_dir):
    """Read directory structure at a specific level (non-recursive) honoring .gitignore rules.
    
    Args:
        path (str): The path to scan.
        work_dir (str): The working directory.
    
    Returns:
        dict: Dictionary with 'dirs' and 'files' lists containing paths relative to work_dir
        
    Raises:
        ValueError: If the requested path is outside the allowed root path or doesn't exist.
    """
    # Get absolute paths for security comparison
    abs_work_dir = os.path.abspath(work_dir)
    abs_path = os.path.abspath(path)
    
    # Security check: ensure the requested path is within the root path
    if not abs_path.startswith(abs_work_dir):
        raise ValueError(f"Security error: Requested path '{path}' is outside the allowed root path.")
    
    if not os.path.exists(path):
        raise ValueError(f"Requested path '{path}' was not found.")

    # Get gitignore spec for the current directory
    spec = load_gitignore_for_directory(path)
    
    # Use glob to get all items in the current directory
    items = glob.glob(os.path.join(path, '*'))
    
    dirs = []
    files = []
    
    # Filter items and classify them as directories or files
    for item in items:
        # Skip if item is ignored by gitignore rules
        if is_ignored(item, path, spec):
            continue
            
        # Get path relative to work_dir
        rel_path = os.path.relpath(item, work_dir)
        
        # Add to appropriate list
        if os.path.isdir(item):
            dirs.append(rel_path)
        else:
            files.append(rel_path)
    
    # Sort for consistent output
    dirs.sort()
    files.sort()
    
    return {
        'dirs': dirs,
        'files': files
    }
