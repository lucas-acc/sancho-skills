#!/usr/bin/env python3
"""
PDF to Text converter using PyMuPDF4LLM
"""

import argparse
import sys
from pathlib import Path

try:
    import pymupdf4llm
except ImportError:
    print("Error: pymupdf4llm is not installed.")
    print("Install it with: pip install pymupdf4llm")
    sys.exit(1)


def convert_pdf_to_text(pdf_path: str, output_path: str = None, markdown: bool = False, page_range: str = None) -> str:
    """
    Convert PDF to text using PyMuPDF4LLM.

    Args:
        pdf_path: Path to the PDF file
        output_path: Output text file path (optional)
        markdown: Whether to output markdown format
        page_range: Page range string like "1-5" or "3" (optional)

    Returns:
        Path to the output file
    """
    pdf_file = Path(pdf_path).expanduser().resolve()

    if not pdf_file.exists():
        print(f"Error: PDF file not found: {pdf_file}")
        sys.exit(1)

    if not pdf_file.suffix.lower() == '.pdf':
        print(f"Error: File is not a PDF: {pdf_file}")
        sys.exit(1)

    # Determine output path
    if output_path is None:
        suffix = ".md" if markdown else ".txt"
        output_file = pdf_file.with_suffix(suffix)
    else:
        output_file = Path(output_path).expanduser().resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

    # Parse page range if provided
    pages = None
    if page_range:
        try:
            if '-' in page_range:
                start, end = page_range.split('-', 1)
                # PyMuPDF uses 0-based indexing, user provides 1-based
                pages = [int(start) - 1, int(end) - 1]
            else:
                # Single page - convert to 0-based index
                page_num = int(page_range) - 1
                pages = [page_num, page_num]
        except ValueError:
            print(f"Error: Invalid page range format: {page_range}")
            print("Use format: '1-5' for range or '3' for single page")
            sys.exit(1)

    print(f"📄 Converting: {pdf_file.name}")

    try:
        # Convert PDF to text
        if pages:
            print(f"   Pages: {page_range}")
            text = pymupdf4llm.to_markdown(
                str(pdf_file),
                pages=pages,
                page_chunks=False
            )
        else:
            text = pymupdf4llm.to_markdown(
                str(pdf_file),
                page_chunks=False
            )

        # Convert to plain text if markdown is not requested
        if not markdown:
            # Simple cleanup to make it more plain-text friendly
            # Remove excessive whitespace but keep paragraph structure
            import re
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text.strip()

        # Write output
        output_file.write_text(text, encoding='utf-8')

        print(f"✅ Saved to: {output_file}")
        print(f"   Size: {len(text):,} characters")

        return str(output_file)

    except Exception as e:
        print(f"Error: Failed to convert PDF: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF files to text using PyMuPDF4LLM"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: same as PDF with .txt extension)"
    )
    parser.add_argument(
        "-m", "--markdown",
        action="store_true",
        help="Output in Markdown format instead of plain text"
    )
    parser.add_argument(
        "-p", "--pages",
        help="Page range to convert (e.g., '1-5' or '3')"
    )

    args = parser.parse_args()

    convert_pdf_to_text(
        pdf_path=args.pdf_path,
        output_path=args.output,
        markdown=args.markdown,
        page_range=args.pages
    )


if __name__ == "__main__":
    main()
