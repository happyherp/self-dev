def validate_repo_name(repo_name: str) -> bool:
    """
    Validate GitHub repository name in the format 'owner/repo'.
    
    Args:
        repo_name: The repository name to validate in 'owner/repo' format
        
    Returns:
        bool: True if the repo name is valid, False otherwise
        
    Examples:
        >>> validate_repo_name("happyherp/self-dev")
        True
        >>> validate_repo_name("invalid")
        False
        >>> validate_repo_name("owner/")
        False
        >>> validate_repo_name("/repo")
        False
        >>> validate_repo_name("owner with spaces/repo")
        False
    """
    # Check if repo_name is a string and not None
    if not isinstance(repo_name, str):
        return False
    
    # Check for spaces - not allowed anywhere
    if ' ' in repo_name:
        return False
    
    # Split by '/' and check we have exactly 2 parts
    parts = repo_name.split('/')
    if len(parts) != 2:
        return False
    
    owner, repo = parts
    
    # Both owner and repo must be non-empty
    if not owner or not repo:
        return False
    
    return True


def do_something_useful() -> None:
    print("Replace this with a utility function")