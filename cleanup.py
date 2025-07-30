#!/usr/bin/env python3
# cleanup.py
import sys
from bs4 import BeautifulSoup, Tag

def split_on_pagebreaks(body_tag):
    pages, current = [], []
    for node in list(body_tag.children):
        if isinstance(node, Tag) and node.name == "hr" and "page-break-after:always" in (node.get("style") or ""):
            pages.append(current)
            current = []
        else:
            current.append(node)
    if current:
        pages.append(current)
    return pages

def collect_used_refs(root):
    used = set()
    for tag in root.find_all(True):
        for attr in ("contextref", "unitref", "footnoteref"):
            v = tag.get(attr)
            if v:
                used.add(v)
    return used

def prune_ix_header(ix_header, used_ids):
    # Safely remove any element with an id that's not used
    for el in list(ix_header.select('[id]')):
        el_id = el.get('id')
        if el_id and el_id not in used_ids:
            el.decompose()

def add_hide_css(soup):
    style = soup.new_tag("style")
    style.string = r"""
/* Hide only the header block */
ix\:header, ix\:header * { display:none !important; }
/* Leave facts visible */
"""
    soup.head.append(style)


def main():
    if len(sys.argv) != 4:
        print("Usage: python cleanup.py input.html output.html PAGE_NO", file=sys.stderr)
        sys.exit(1)

    in_path, out_path, page_str = sys.argv[1:]
    page_no = int(page_str)

    with open(in_path, encoding="windows-1252", errors="replace") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    body = soup.body
    if not body:
        raise SystemExit("No <body> tag found.")

    ix_header = soup.find("ix:header")

    pages = split_on_pagebreaks(body)
    if not (1 <= page_no <= len(pages)):
        raise SystemExit(f"Page {page_no} out of range (1..{len(pages)}).")
    page_nodes = pages[page_no - 1]

    # Build new doc
    new = BeautifulSoup("<html><head></head><body></body></html>", "lxml")
    if soup.html and soup.html.head:
        new.html.head.replace_with(soup.html.head)

    add_hide_css(new)

    if ix_header:
        wrapper = new.new_tag("div", style="display:none")
        wrapper.append(ix_header)
        new.body.append(wrapper)

    for n in page_nodes:
        new.body.append(n)

    if ix_header:
        used_ids = collect_used_refs(new.body)
        prune_ix_header(ix_header, used_ids)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(str(new))

    print(f"Saved {out_path} (page {page_no}/{len(pages)}).")

if __name__ == "__main__":
    main()
