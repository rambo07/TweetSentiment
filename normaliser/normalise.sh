#!/bin/bash

# Global definitions
# Error output
ERRORPUT=/dev/stderr
# Current directory
DIR_SCRIPT=$(dirname $(readlink -f $0))
DIR_DATA="$DIR_SCRIPT/data/"
# Default values
DEFAULT_INPUT=/dev/stdin
DEFAULT_OUTPUT=/dev/stdout
# Prints usage instructions
function print_usage()
{
  echo "Usage: $(basename $0) [input [output]]" >> "$ERRORPUT"
  echo "  input      TSV file in Cara input format"
  echo "  output     text file with the normalised text"
}

# Parsing parameters
input="$DEFAULT_INPUT"
output="$DEFAULT_OUTPUT"
# Parse options
while getopts "h" opt
do
  case "$opt" in
    h) print_usage; exit 0;;
    *) print_usage; exit 2;;
  esac
done
shift $((OPTIND - 1))
# Parse positional arguments
if [ $# -gt 2 ]; then print_usage; exit 2; fi
if [ $# -ge 1 ]
then
  input="$1"
  if [ ! -e "$input" ]; then echo "Error: File '$input' could not be opened." >> "$ERRORPUT"; exit 1; fi
fi
if [ $# -eq 2 ]; then output="$2"; fi

cat "$input" | \

# Extracting raw text
#cut -f1 | python $DIR_SCRIPT/xml2txt.py | \

# Replacing special spaces
python $DIR_SCRIPT/fix-0x0a0-space.py | \

# Replacing abbreviations and similar things
python $DIR_SCRIPT/cleanTextMod.py - $DIR_DATA/emoticonListMod.txt $DIR_DATA/one2oneReplace.txt $DIR_DATA/one2manyReplaceMod.txt | \

# Replacing signs
python $DIR_SCRIPT/chsigns.py --raw | \

# Replacing quotes
python $DIR_SCRIPT/chquote.py --raw --anywhere --separate | \

# Tokenising
python $DIR_SCRIPT/txt2sgml.py --raw --abbr $DIR_DATA/my-abbr.txt | \

# Escaping brackets
python $DIR_SCRIPT/escape-all-brackets.py > "$output"

exit 0
