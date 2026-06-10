#!/bin/bash

# Change extension to .gnos so any extension can be passed to the script
# This simply makes it possible to use the path of the associated .solution, .sgf. or .json
file="${1%.*}.gnos"
# Exchange color characters, Black is @ and White is !
tr '@!' '!@' < $file > $file.tmp && mv $file.tmp $file
