# SpaceLens
See where your storage goes. A small Python tool that scans folder metadata and creates a standalone HTML report.

## Features
- Native folder picker or command-line path.
- Largest files, top-level folder totals, and totals by extension.
- Dark responsive HTML report with size bars.
- No third-party Python packages, accounts, uploads, or file-content reads.
- Skips symbolic links, Windows junctions/reparse points, and special files.
- Reports unreadable entries and partial totals.
- Never deletes, moves, or overwrites your files. The only write is a new report.

## Requirements
Python 3.10 or newer. The optional folder picker needs Tkinter, included with standard Windows Python installations. On Linux, install your distribution's python3-tk package or pass a folder path instead.

## Quick start
Download and extract this repository. Open a terminal in the extracted folder.

Windows:
    py spacelens.py

macOS / Linux:
    python3 spacelens.py

Choose a folder in the picker. The terminal displays the saved HTML report path. Open that report in your browser. The report is created in the terminal's current working folder.

You can also specify paths:
    py spacelens.py "C:\Users\YourName\Downloads" --output downloads-report.html
    python3 spacelens.py ~/Downloads --top 30 --output downloads-report.html

Use a new output filename each time; existing files are never overwritten. Parent directories for the output must already exist. Ctrl+C cancels scanning. Large folders may take time; keep the terminal open.

## Example
Open examples/sample-report.html for a report made from fictional sample data.

## Understanding totals
Sizes are logical file lengths, not actual allocated disk space. Sparse files, compression, and hard links can make disk usage differ. Hard-linked files count once per path. Folder bars group each immediate child folder including descendants; "(root files)" covers files directly in the selected folder. Charts show the largest 15 groups, with percentages of the full scanned total. Empty folders have no size entry. Extension grouping uses the final suffix, case-insensitively.

A scan is not a filesystem snapshot. Files may change or disappear while scanning, and the tool cannot guarantee protection from adversarial filesystem changes. Use it on folders you control. An unreadable entry is reported and omitted from totals.

## Privacy
No network calls or telemetry. Reports contain relative file/folder names and the selected folder's basename. Review these before sharing. Real reports are ignored by .gitignore by default; the example contains fictional names.

## Publish on GitHub
Upload this folder's contents to a new repository named SpaceLens, including .github and .gitignore. Suggested repository description:
A lightweight Python disk usage analyzer with largest-file rankings and standalone HTML reports. No dependencies or uploads.

GitHub Pages can display the sample HTML report, but it cannot run the Python scanner. Users download the source and run it locally with Python.

## Tests
    python -m unittest discover -s tests -v

The GitHub Actions workflow runs tests on Windows and Ubuntu with Python 3.10 and 3.13.

## License
MIT. See LICENSE.
