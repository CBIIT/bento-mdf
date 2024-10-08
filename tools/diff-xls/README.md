# NAME

flat-model-diff-xls.pl - Make a nice Excel showing model flatfile differences

# SYNOPSIS

    Usage: perl flat-model-diff-xls.pl [--commits <commit range>]
                     [--outfile <output.xls>] [--skip <n>]

    # in a model repo directory:
    # create a diff excel file with the latest changes
    $ perl flat-model-diff-xls.pl # creates diff.xlsx
    # create a diff excel from the previous changeset
    $ perl flat-model-diff-xls.pl --skip 1 # creates diff.xlsx
    # create a diff excel from the commit range in new-diff.xlsx
    $ perl flat-model-diff-xls.pl --commits 51918c8..77bd441 --outfile new-diff.xlsx

# DESCRIPTION

This script generates an Excel file that tabulates the nodes, relationships, 
properties, and value sets of a Bento model. The Excel file contains rows in 
a strikethrough face to indicate removed records, and rows in a yellow highlight
face to indicate added records. 

"Removed" and "added" are relative to either the last time the model
flatfile was changed (according to `git log`), the nth-to-last time,
(`--skip=n`) or according to a pair of commits provided to the
command line option `--commits`.

This script depends on the existence of the file 

    docs/model-desc/<model-name>model.txt

in the GitHub pages directory of a Bento model repository. This file
should be generated by continuous integration (Travis CI) each time
the model master branch is updated.

# AUTHOR

    Mark A. Jensen < mark -dot- jensen -at- nih -dot- com >
    FNLCR
    2020