TEST_CONVERT_URLS = [
    # look like (input_url, expected_output_url)
    (
        "https://github.com/user/repo/blob/main/path/to/file.txt",
        "https://raw.githubusercontent.com/user/repo/main/path/to/file.txt",
    ),
    (
        "https://github.com/user/repo/blob/master/path/to/file.txt",
        "https://raw.githubusercontent.com/user/repo/master/path/to/file.txt",
    ),
    (
        "https://github.com/user/repo/blob/feature-branch/path/to/file.txt",
        "https://raw.githubusercontent.com/user/repo/feature-branch/path/to/file.txt",
    ),
    (
        "https://github.com/user/repo/blob/main/folder1/folder2/file.txt",
        "https://raw.githubusercontent.com/user/repo/main/folder1/folder2/file.txt",
    ),
    (
        "https://github.com/user/repo/blob/v1.0.0/path/to/file.txt",
        "https://raw.githubusercontent.com/user/repo/v1.0.0/path/to/file.txt",
    ),
    (
        "https://github.com/user/repo/blob/abc123def456/path/to/file.txt",
        "https://raw.githubusercontent.com/user/repo/abc123def456/path/to/file.txt",
    ),
    (
        "https://github.com/user/repo/blob/feature/new-feature/path/to/file.txt",
        "https://raw.githubusercontent.com/user/repo/feature/new-feature/path/to/file.txt",
    ),
    (
        "https://github.com/user/repo/blob/version-1.0/path/to/file.txt",
        "https://raw.githubusercontent.com/user/repo/version-1.0/path/to/file.txt",
    ),
    (
        "https://github.com/user/repo/blob/main/path/to/file with spaces.txt",
        "https://raw.githubusercontent.com/user/repo/main/path/to/file with spaces.txt",
    ),
    (
        "https://github.com/user/repo/blob/main/path/to/file%20with%20encoded%20spaces.txt",
        "https://raw.githubusercontent.com/user/repo/main/path/to/file%20with%20encoded%20spaces.txt",
    ),
    (
        "https://github.com/user/repo/blob/main/path/to/特殊字符.txt",
        "https://raw.githubusercontent.com/user/repo/main/path/to/特殊字符.txt",
    ),
    (
        "https://github.com/user/repo/blob/main/path/to/file_with_underscores.txt",
        "https://raw.githubusercontent.com/user/repo/main/path/to/file_with_underscores.txt",
    ),
    (
        "https://github.com/user/repo/blob/main/path/to/file-with-dashes.txt",
        "https://raw.githubusercontent.com/user/repo/main/path/to/file-with-dashes.txt",
    ),
    (
        "https://github.company.com/user/repo/blob/main/path/to/file.txt",
        "https://github.company.com/user/repo/blob/main/path/to/file.txt",
    ),  # Should not transform
    (
        "https://github.com/user/repo",
        "https://github.com/user/repo",
    ),  # Should not transform
    (
        "https://github.com/user/repo/tree/main/folder1",
        "https://github.com/user/repo/tree/main/folder1",
    ),  # Should not transform
]
