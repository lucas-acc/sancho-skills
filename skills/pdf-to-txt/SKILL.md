---
name: pdf-to-txt
description: Convert PDF files to plain text using PyMuPDF4LLM
metadata:
  openclaw:
    emoji: 📄
    requires:
      bins: ["python3"]
      python_packages: ["pymupdf4llm"]
    install:
      - id: "pip-pymupdf4llm"
        kind: "pip"
        command: "pip install pymupdf4llm"
        label: "Install PyMuPDF4LLM via pip"
---

# PDF to Text Skill

Convert PDF files to plain text format using PyMuPDF4LLM. This tool extracts text content from PDF documents while preserving the reading order and basic formatting.

## Features

- Extract text from any PDF file
- Preserve reading order and structure
- Support for multi-page documents
- Optional Markdown output with formatting hints

## Usage

### Basic Conversion

Convert a PDF to text file:

```bash
python {baseDir}/scripts/convert.py "<pdf_path>"
```

Output will be saved as `<pdf_filename>.txt` in the same directory as the PDF.

### Specify Output Path

```bash
python {baseDir}/scripts/convert.py "<pdf_path>" --output "~/Documents/output.txt"
```

### Convert with Markdown Formatting

Use `--markdown` flag to get Markdown-formatted output with headers, lists, and other formatting hints:

```bash
python {baseDir}/scripts/convert.py "<pdf_path>" --markdown
```

### Page Range Selection

Convert only specific pages:

```bash
# Convert pages 1-10 only
python {baseDir}/scripts/convert.py "<pdf_path>" --pages 1-10

# Convert single page
python {baseDir}/scripts/convert.py "<pdf_path>" --pages 5
```

## Examples

```bash
# Basic conversion
python {baseDir}/scripts/convert.py "~/Documents/paper.pdf"
# Output: ~/Documents/paper.txt

# With custom output path
python {baseDir}/scripts/convert.py "~/Documents/paper.pdf" --output "~/Notes/paper_content.txt"

# Markdown output
python {baseDir}/scripts/convert.py "~/Documents/paper.pdf" --markdown --output "~/Notes/paper.md"

# Convert first 5 pages only
python {baseDir}/scripts/convert.py "~/Documents/book.pdf" --pages 1-5 --output "~/Notes/chapter1.txt"
```

## Output Format

### Plain Text (default)
- Clean text extraction
- Preserves paragraph breaks
- Removes decorative formatting

### Markdown (`--markdown`)
- Headers marked with `#`
- Lists preserved with `-` or `*`
- Bold/italic formatting hints where detectable
- Better for documents with complex structure

## Troubleshooting

### "No text found in PDF"

- The PDF may be scanned images without OCR
- Try using OCR tools first to add a text layer

### Garbled text

- The PDF may use custom fonts without proper encoding
- Some PDFs have text stored in unexpected ways

### Missing content

- Complex layouts (multi-column, sidebars) may lose some positioning
- Forms and interactive elements may not extract cleanly
