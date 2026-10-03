"""Scenario s6: sparse Go tool 'grepl' (create mode, thin evidence)."""
from fixture import w

ROOT = "s6-grepl"


def build(base):
    r = base / ROOT
    w(r / "go.mod", "module github.com/example-org/grepl\n\ngo 1.22\n")
    w(r / "main.go", '''\
// grepl prints the lines of standard input that match a regular expression.
package main

import (
\t"bufio"
\t"flag"
\t"fmt"
\t"os"
\t"regexp"
)

func main() {
\tignoreCase := flag.Bool("i", false, "case-insensitive match")
\tinvert := flag.Bool("v", false, "print lines that do not match")
\tflag.Parse()
\tif flag.NArg() != 1 {
\t\tfmt.Fprintln(os.Stderr, "usage: grepl [-i] [-v] PATTERN < input")
\t\tos.Exit(2)
\t}
\tpattern := flag.Arg(0)
\tif *ignoreCase {
\t\tpattern = "(?i)" + pattern
\t}
\tre, err := regexp.Compile(pattern)
\tif err != nil {
\t\tfmt.Fprintln(os.Stderr, "grepl:", err)
\t\tos.Exit(2)
\t}
\tscanner := bufio.NewScanner(os.Stdin)
\tmatched := false
\tfor scanner.Scan() {
\t\tline := scanner.Text()
\t\tif re.MatchString(line) != *invert {
\t\t\tfmt.Println(line)
\t\t\tmatched = true
\t\t}
\t}
\tif !matched {
\t\tos.Exit(1)
\t}
}
''')
    w(r / ".gitignore", "grepl\ngrepl.exe\n")
