#!/usr/bin/env python3
"""
Convert arXiv HTML papers (LaTeXML-generated) to Markdown.

This script handles:
- Document structure (title, authors, abstract)
- Sections and subsections
- Paragraphs and text formatting
- Mathematical equations (MathML to LaTeX)
- Tables
- Figures and captions
- Citations
- Algorithms/listings
- References
"""

import re
import sys
from pathlib import Path
from html import unescape
from typing import Optional

try:
    from bs4 import BeautifulSoup, NavigableString
except ImportError:
    print("Error: BeautifulSoup4 is required. Install with: pip install beautifulsoup4")
    sys.exit(1)


class ArxivHTMLToMarkdown:
    def __init__(self):
        self.output_lines = []
        self.figure_counter = 0
        self.table_counter = 0
        self.equation_counter = 0

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        # Unescape HTML entities
        text = unescape(text)
        return text

    def extract_math(self, math_elem) -> str:
        """Extract LaTeX from MathML element."""
        if not math_elem:
            return ""

        # Try to get annotation (LaTeX source)
        annotation = math_elem.find('annotation', encoding='application/x-tex')
        if annotation:
            return annotation.get_text().strip()

        # Try alttext attribute
        alttext = math_elem.get('alttext', '')
        if alttext:
            return alttext

        # Fallback: try to extract from semantics
        semantics = math_elem.find('semantics')
        if semantics:
            annotation = semantics.find(
                'annotation', encoding='application/x-tex')
            if annotation:
                return annotation.get_text().strip()

        # Last resort: get all text
        text = math_elem.get_text()
        return self.clean_text(text)

    def process_math(self, elem) -> str:
        """Process math elements, converting to LaTeX format."""
        math_elements = elem.find_all('math')
        if not math_elements:
            return ""

        result = []
        for math in math_elements:
            latex = self.extract_math(math)
            if latex:
                # Check if it's display math (block equation)
                display = math.get('display', 'inline')
                if display == 'block' or display == 'display':
                    result.append(f"\n$$\n{latex}\n$$\n")
                else:
                    result.append(f" ${latex}$ ")

        return "".join(result)

    def process_text_with_math(self, elem) -> str:
        """Process text content, handling math inline."""
        if not elem:
            return ""

        # First, replace math elements with placeholders
        math_placeholders = {}
        math_counter = 0
        for math in elem.find_all('math'):
            latex = self.extract_math(math)
            if latex:
                placeholder = f"__MATH_{math_counter}__"
                math_placeholders[placeholder] = f" ${latex}$ "
                math.replace_with(placeholder)
                math_counter += 1

        # Process citations
        for cite in elem.find_all('cite', class_='ltx_cite'):
            cite_text = self.process_citation(cite)
            if cite_text:
                cite.replace_with(cite_text)

        # Process links
        for link in elem.find_all('a'):
            classes = link.get('class', [])
            if 'ltx_href' in classes:
                # External link
                href = link.get('href', '')
                link_text = self.clean_text(link.get_text())
                if href and link_text:
                    link.replace_with(f"[{link_text}]({href})")
                elif link_text:
                    link.replace_with(link_text)
            elif 'ltx_ref' in classes:
                # Internal reference
                ref_text = self.clean_text(link.get_text())
                if ref_text:
                    link.replace_with(ref_text)

        # Get all text
        text = elem.get_text(separator=' ', strip=False)

        # Replace math placeholders
        for placeholder, math_expr in math_placeholders.items():
            text = text.replace(placeholder, math_expr)

        # Clean up
        text = self.clean_text(text)
        # Clean up multiple spaces
        text = re.sub(r' +', ' ', text)
        # Clean up spaces around math
        # text = re.sub(r' \$', '$', text)
        # text = re.sub(r'\$ ', '$', text)
        return text.strip()

    def process_paragraph(self, para_elem) -> str:
        """Process a paragraph element."""
        if not para_elem:
            return ""

        # Handle math and text together
        text = self.process_text_with_math(para_elem)

        # Handle formatting - find all bold elements
        bold_elements = para_elem.find_all(['b', 'strong'])
        bold_elements.extend(para_elem.find_all(
            class_=re.compile('ltx_font_bold')))
        for bold in bold_elements:
            bold_text = bold.get_text()
            if bold_text:
                text = text.replace(bold_text, f"**{bold_text}**")

        # Find all italic elements
        italic_elements = para_elem.find_all(['i', 'em'])
        italic_elements.extend(para_elem.find_all(
            class_=re.compile('ltx_font_italic')))
        for italic in italic_elements:
            italic_text = italic.get_text()
            if italic_text:
                text = text.replace(italic_text, f"*{italic_text}*")

        # Find all code elements
        code_elements = para_elem.find_all(['code', 'tt'])
        code_elements.extend(para_elem.find_all(
            class_=re.compile('ltx_font_typewriter')))
        for code in code_elements:
            code_text = code.get_text()
            if code_text:
                text = text.replace(code_text, f"`{code_text}`")

        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def process_table(self, table_elem) -> str:
        """Convert HTML table to Markdown table."""
        if not table_elem:
            return ""

        self.table_counter += 1
        result = []

        # Find the actual table (might be nested)
        actual_table = table_elem.find('table')
        if not actual_table:
            # Check if it's an SVG table (rendered as image)
            svg = table_elem.find('svg')
            if svg:
                # For SVG tables, just note that it's a table
                return "*[Table rendered as image]*"
            actual_table = table_elem

        # Get headers
        headers = []
        thead = actual_table.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    cell_text = self.process_text_with_math(th)
                    # Clean up cell text
                    cell_text = cell_text.strip()
                    if not cell_text:
                        cell_text = " "
                    headers.append(cell_text)
        else:
            # Try first row as headers
            first_row = actual_table.find('tr')
            if first_row:
                for th in first_row.find_all(['th', 'td']):
                    cell_text = self.process_text_with_math(th)
                    cell_text = cell_text.strip()
                    if not cell_text:
                        cell_text = " "
                    headers.append(cell_text)

        if not headers:
            return ""

        # Build markdown table
        result.append("| " + " | ".join(headers) + " |")
        result.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Get body rows
        tbody = actual_table.find('tbody')
        rows = tbody.find_all('tr') if tbody else actual_table.find_all('tr')

        # Skip header row if no thead
        if not thead and rows:
            rows = rows[1:]

        for row in rows:
            cells = []
            for cell in row.find_all(['td', 'th']):
                cell_text = self.process_text_with_math(cell)
                # Clean up cell text
                cell_text = cell_text.strip()
                if not cell_text:
                    cell_text = " "
                # Escape pipe characters
                cell_text = cell_text.replace('|', '\\|')
                # Replace newlines with spaces
                cell_text = cell_text.replace('\n', ' ')
                cells.append(cell_text)
            if cells:
                # Pad cells if needed
                while len(cells) < len(headers):
                    cells.append(" ")
                result.append("| " + " | ".join(cells[:len(headers)]) + " |")

        return "\n".join(result)

    def process_figure(self, figure_elem) -> str:
        """Process figure element."""
        if not figure_elem:
            return ""

        self.figure_counter += 1
        result = []

        # Get caption
        caption = figure_elem.find('figcaption')
        if caption:
            caption_text = self.process_text_with_math(caption)
            # Extract figure number
            fig_tag = caption.find(class_=re.compile('ltx_tag_figure'))
            if fig_tag:
                fig_num = self.clean_text(fig_tag.get_text())
                caption_text = caption_text.replace(fig_num, "").strip()
                result.append(f"**{fig_num}** {caption_text}")
            else:
                result.append(
                    f"**Figure {self.figure_counter}:** {caption_text}")
        else:
            result.append(f"**Figure {self.figure_counter}**")

        # Get image if present
        img = figure_elem.find('img')
        if img:
            src = img.get('src', '')
            alt = img.get('alt', 'Figure')
            result.append(f"![{alt}]({src})")

        return "\n\n".join(result)

    def process_equation(self, eq_elem) -> str:
        """Process equation element."""
        if not eq_elem:
            return ""

        self.equation_counter += 1

        # Find math element
        math = eq_elem.find('math')
        if not math:
            return ""

        latex = self.extract_math(math)
        if not latex:
            return ""

        # Get equation number
        eqno = eq_elem.find(class_=re.compile('ltx_tag_equation'))
        eq_num = ""
        if eqno:
            eq_num = f"\\tag{{{self.clean_text(eqno.get_text())}}}"

        return f"\n$$\n{latex}{eq_num}\n$$\n"

    def process_algorithm(self, alg_elem) -> str:
        """Process algorithm/listing element."""
        if not alg_elem:
            return ""

        result = []

        # Get caption
        caption = alg_elem.find('figcaption')
        if caption:
            caption_text = self.process_text_with_math(caption)
            result.append(f"**{caption_text}**")

        # Get listing lines
        listing = alg_elem.find(class_='ltx_listing')
        if listing:
            lines = listing.find_all(class_='ltx_listingline')
            code_lines = []
            for line in lines:
                # Process the entire line (text, math, line numbers, etc.)
                line_text = self.process_text_with_math(line)
                line_text = line_text.strip()
                if line_text:
                    code_lines.append(line_text)

            if code_lines:
                result.append("```")
                result.append("\n".join(code_lines))
                result.append("```")

        return "\n\n".join(result)

    def process_citation(self, cite_elem) -> str:
        """Process citation element."""
        if not cite_elem:
            return ""

        # Extract citation text - look for ref tags
        refs = cite_elem.find_all('a', class_='ltx_ref')
        citations = []

        for ref in refs:
            ref_text = self.clean_text(ref.get_text())
            if ref_text:
                citations.append(ref_text)

        # If no refs found, try to get text from cite tag
        if not citations:
            cite_text = self.clean_text(cite_elem.get_text())
            if cite_text:
                # Remove parentheses if present
                cite_text = cite_text.strip('()')
                citations.append(cite_text)

        if citations:
            return f"({', '.join(citations)})"
        return ""

    def process_section(self, section_elem, level: int = 1) -> None:
        """Process a section element recursively."""
        if not section_elem:
            return

        # Get section title
        title_elem = section_elem.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
                                       class_=re.compile('ltx_title'))
        if title_elem:
            # Get the tag (section number) separately
            tag_elem = title_elem.find(class_=re.compile('ltx_tag'))
            tag_text = ""
            if tag_elem:
                tag_text = self.clean_text(tag_elem.get_text())

            # Get the title text (everything except the tag)
            title_text = ""
            for child in title_elem.children:
                if hasattr(child, 'name') and child.name:
                    if 'ltx_tag' not in child.get('class', []):
                        child_text = self.process_text_with_math(child)
                        if child_text:
                            title_text += child_text + " "
                elif isinstance(child, str):
                    text = self.clean_text(child)
                    if text and text != tag_text:
                        title_text += text + " "

            title_text = title_text.strip()

            # If we have a tag, prepend it
            if tag_text and title_text:
                title_text = f"{tag_text} {title_text}"
            elif tag_text:
                title_text = tag_text

            # Determine markdown header level
            header_level = min(level, 6)
            if title_text:
                self.output_lines.append(
                    f"\n{'#' * header_level} {title_text}\n")

        # Process content in order
        for child in section_elem.children:
            if not hasattr(child, 'name') or child.name is None:
                continue

            class_names = child.get('class', []) if hasattr(
                child, 'get') else []
            class_str = ' '.join(class_names) if class_names else ''

            # Paragraphs
            if child.name == 'p' or 'ltx_para' in class_str:
                para_text = self.process_paragraph(child)
                if para_text:
                    self.output_lines.append(para_text + "\n\n")

            # Algorithms (check before regular figures)
            elif child.name == 'figure' and 'ltx_float_algorithm' in class_str:
                alg_text = self.process_algorithm(child)
                if alg_text:
                    self.output_lines.append(f"\n{alg_text}\n")

            # Figures
            elif child.name == 'figure' or 'ltx_figure' in class_str:
                fig_text = self.process_figure(child)
                if fig_text:
                    self.output_lines.append(f"\n{fig_text}\n")

            # Tables
            elif child.name in ['table', 'figure'] and 'ltx_table' in class_str:
                table_text = self.process_table(child)
                if table_text:
                    # Get caption
                    caption = child.find('figcaption')
                    if caption:
                        caption_text = self.process_text_with_math(caption)
                        self.output_lines.append(f"\n**{caption_text}**\n\n")
                    self.output_lines.append(f"{table_text}\n")

            # Equations
            elif 'ltx_equation' in class_str or 'ltx_equationgroup' in class_str:
                eq_text = self.process_equation(child)
                if eq_text:
                    self.output_lines.append(eq_text)

            # Subsections
            elif child.name == 'section' and 'ltx_subsection' in class_str:
                self.process_section(child, level + 1)

            # Nested sections
            elif child.name == 'section':
                self.process_section(child, level + 1)

        # Process any remaining paragraphs that weren't caught
        processed_paras = set()
        for para in section_elem.find_all('p', class_='ltx_p', recursive=False):
            para_id = para.get('id', '')
            if para_id not in processed_paras:
                para_text = self.process_paragraph(para)
                if para_text:
                    # Check if this paragraph was already added
                    if not self.output_lines or para_text not in self.output_lines[-1]:
                        self.output_lines.append(para_text + "\n\n")
                        processed_paras.add(para_id)

    def convert(self, html_content: str) -> str:
        """Convert HTML content to Markdown."""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Reset counters
        self.figure_counter = 0
        self.table_counter = 0
        self.equation_counter = 0
        self.output_lines = []

        # Extract title
        title_elem = soup.find('title')
        if title_elem:
            title = self.clean_text(title_elem.get_text())
            self.output_lines.append(f"# {title}\n")

        # Extract authors
        authors_elem = soup.find('div', class_='ltx_authors')
        if authors_elem:
            authors = []
            for author in authors_elem.find_all(class_='ltx_personname'):
                author_name = self.clean_text(author.get_text())
                if author_name:
                    authors.append(author_name)
            if authors:
                self.output_lines.append(
                    f"\n**Authors:** {', '.join(authors)}\n")

        # Extract abstract
        abstract_elem = soup.find('div', class_='ltx_abstract')
        if abstract_elem:
            abstract_paras = []
            for para in abstract_elem.find_all('p', class_='ltx_p'):
                para_text = self.process_paragraph(para)
                if para_text:
                    abstract_paras.append(para_text)
            if abstract_paras:
                abstract_text = "\n\n".join(abstract_paras)
                self.output_lines.append(f"\n## Abstract\n\n{abstract_text}\n")

        # Extract keywords
        keywords_elem = soup.find('div', class_='ltx_keywords')
        if keywords_elem:
            keywords = self.clean_text(keywords_elem.get_text())
            if keywords:
                self.output_lines.append(f"\n**Keywords:** {keywords}\n")

        # Find main article content
        article = soup.find('article', class_='ltx_document')
        if not article:
            article = soup.find('div', class_='ltx_page_content')
        if not article:
            article = soup.find('body')

        if article:
            # Find all top-level sections
            # We look for sections that are not contained within other sections
            all_sections = article.find_all(['section', 'div'],
                                           class_=re.compile(r'ltx_(section|appendix|bibliography)'))
            
            processed_sections = set()
            
            for section in all_sections:
                # Skip if this section is inside another section we will process
                is_nested = False
                parent = section.parent
                while parent and parent != article:
                    if parent.name == 'section' or (parent.name == 'div' and any(c.startswith('ltx_section') or c == 'ltx_appendix' for c in parent.get('class', []))):
                        is_nested = True
                        break
                    parent = parent.parent
                
                if is_nested:
                    continue

                section_id = section.get('id', str(id(section)))
                if section_id in processed_sections:
                    continue
                
                class_list = section.get('class', [])
                if 'ltx_bibliography' in class_list:
                    continue # Handle bibliography separately at the end
                
                if 'ltx_appendix' in class_list:
                    self.process_section(section, level=1)
                    processed_sections.add(section_id)
                elif 'ltx_section' in class_list or section.name == 'section':
                    self.process_section(section, level=1)
                    processed_sections.add(section_id)

            # Process bibliography if present
            bibliography = article.find(['section', 'div'], class_='ltx_bibliography')
            if bibliography:
                self.output_lines.append("\n## References\n")
                for bib_item in bibliography.find_all('li', class_='ltx_bibitem'):
                    bib_text = self.process_text_with_math(bib_item)
                    if bib_text:
                        self.output_lines.append(f"- {bib_text}\n")

        # Join all lines and clean up
        markdown = "\n".join(self.output_lines)

        # Clean up multiple blank lines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Clean up spaces around math
        markdown = re.sub(r'\s+\$', ' $', markdown)
        markdown = re.sub(r'\$\s+', '$ ', markdown)

        # Clean up whacky backticks
        markdown = re.sub(r'````', '`', markdown)
        markdown = re.sub(fr'`{2,}', '`', markdown)

        # Remove backticks from link URLs in Markdown links
        # Pattern: [text](url) where url may contain stray backticks
        def replace_url_backticks(match):
            text = match.group(1).replace('`', '')
            url = match.group(2).replace('`', '')
            return f"[{text}]({url})"

        markdown = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',
                          replace_url_backticks, markdown)

        # Remove stray spaces before punctuation
        markdown = re.sub(r'\s+([.,:;?!])', r'\1', markdown)

        # Remove stray spaces inside parentheses
        markdown = re.sub(r'\(\s+', r'(', markdown)
        markdown = re.sub(r'\s+\)', r')', markdown)

        return markdown.strip()


def html_to_markdown(html_content: str) -> str:
    """
    Convert HTML content to Markdown.

    Convenience function for programmatic use.

    Args:
        html_content: HTML string to convert

    Returns:
        Markdown string
    """
    converter = ArxivHTMLToMarkdown()
    return converter.convert(html_content)


def html_file_to_markdown(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert HTML file to Markdown file.

    Convenience function for file-based conversion.

    Args:
        input_path: Path to input HTML file
        output_path: Optional path to output Markdown file. 
                     If None, uses input_path with .md extension.

    Returns:
        Path to output file as a string

    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    converter = ArxivHTMLToMarkdown()
    markdown = converter.convert(html_content)

    if output_path is None:
        output_file = input_file.with_suffix('.md')
    else:
        output_file = Path(output_path)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    return str(output_file)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python html_to_markdown.py <input.html> [output.md]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    # Read HTML
    with open(input_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Convert
    converter = ArxivHTMLToMarkdown()
    markdown = converter.convert(html_content)

    # Write output
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix('.md')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"Converted {input_path} to {output_path}")


if __name__ == '__main__':
    main()
