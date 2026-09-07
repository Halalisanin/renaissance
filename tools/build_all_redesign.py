#!/usr/bin/env python3
"""Redesigned ALL-format generator (memoir design + cover page).

Regenerates every digital book format with the approved memoir design
(EB Garamond, warm palette, cover page connected to the body), writing to:

    book_formats/<FMT>/book.<ext>

Print interiors (print/, book_formats/print/) are untouched — they stay
cover-less by design.

Formats:
  HTML      memoir HTML (screen-adapted) with cover page
  PDF       A5 memoir PDF with cover page (Chrome)
  EPUB      pandoc EPUB with memoir CSS + embedded cover
  DOCX      python-docx memoir-styled document with cover image
  ODT       pandoc ODT
  RTF       pandoc RTF
  FB2       pandoc FB2
  Markdown  structured markdown from JSON
  TXT       plain text from JSON

Requires: pandoc, python-docx, Chrome (headless).
"""
import os, re, html, json, subprocess, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_print_redesign as bp

ROOT = bp.ROOT
CONTENT_JSON = bp.CONTENT_JSON
CHROME = bp.CHROME
TITLE = bp.TITLE
AUTHOR = bp.AUTHOR
ISBN_PRINT = bp.ISBN_PRINT
ISBN_ELEC = '978-1-0492-8329-6'
SUBTITLE = 'A journey through the many faces of the human spirit'
COVER = 'cover1.png'
COVER_DIR = os.path.join(ROOT, 'book_design')
BOOK_FORMATS = os.path.join(ROOT, 'book_formats')

# ---------------------------------------------------------------------------
# CSS variants
# ---------------------------------------------------------------------------
# Screen-adapted memoir CSS: same design language, responsive for reading.
DIGITAL_CSS = bp.PRINT_CSS + """
@media screen{
  html,body{ background:#FBF8F1; }
  body{ max-width:740px; margin:0 auto; padding:56px 28px 96px; }
  .cover-page{ position:relative; width:100%; height:auto; aspect-ratio:148/210; }
  .cover-page img{ position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; }
  .title-page{ padding-top:18mm; }
  .copyright-page{ padding-top:14mm; }
  .fm{ padding-top:12mm; }
  .contents{ padding-top:10mm; }
  .part{ padding-top:20mm; }
  .about{ padding-top:10mm; }
  .back-cover{ padding-top:12mm; }
}
"""

# Reflowable memoir CSS for EPUB (no @page, no fixed mm page geometry).
EPUB_CSS = """
*{ box-sizing:border-box; margin:0; padding:0; }
body{
  font-family:'EB Garamond',Georgia,'Times New Roman',serif;
  background:#FBF8F1; color:#403A31;
  font-size:1em; line-height:1.9;
}
/* cover page (connected to body) */
.cover-page{ text-align:center; margin:0 0 2em; page-break-after:always; }
.cover-page img{ width:100%; max-width:100%; height:auto; display:block; }
/* title page */
.title-page{ text-align:center; padding-top:4em; page-break-after:always; }
.title-page .kicker{ font-size:.62em; letter-spacing:.3em; text-transform:uppercase; color:#A67C52; margin-bottom:2.2em; }
.title-page h1{ font-family:'EB Garamond',Georgia,serif; font-size:1.9em; font-weight:400; color:#2C2822; line-height:1.14; margin:0 0 .5em; }
.title-page h1 em{ font-style:italic; color:#A67C52; }
.title-page .sub{ font-style:italic; font-size:.95em; color:#8B8172; margin:0 0 2.8em; line-height:1.5; }
.title-page .by{ letter-spacing:.26em; text-transform:uppercase; font-size:.72em; color:#2C2822; }
/* copyright */
.copyright-page{ padding-top:4em; text-align:center; font-size:.72em; color:#403A31; line-height:1.75; page-break-after:always; }
.copyright-page .lstext{ text-align:justify; font-size:.82em; margin:1.6em 2em; color:#8B8172; }
.copyright-page strong{ color:#2C2822; }
/* front matter */
.fm{ text-align:center; padding-top:3em; page-break-after:always; }
.fm-label{ font-size:.62em; letter-spacing:.28em; text-transform:uppercase; color:#A67C52; margin-bottom:2.2em; }
.ornament{ color:#C9A87C; font-size:.9em; margin-bottom:1.8em; letter-spacing:.4em; }
.dedication-text,.for-every-soul-text{ font-style:italic; font-size:.95em; color:#403A31; max-width:34em; margin:0 auto; line-height:2; }
.prayer .zulu{ font-size:1.15em; font-style:italic; color:#2C2822; }
.prayer .english{ color:#8B8172; margin-top:1.1em; font-size:.85em; }
.prayer .attr{ font-size:.62em; letter-spacing:.2em; text-transform:uppercase; color:#A67C52; margin-top:1.6em; }
.fm-body{ text-align:left; max-width:36em; margin:0 auto; }
.fm-body p{ margin-bottom:1.15em; text-align:justify; }
.fm-body .signoff{ margin-top:2em; font-style:italic; color:#A67C52; text-align:right; }
.fm-body .signoff .place{ display:block; font-size:.62em; letter-spacing:.2em; text-transform:uppercase; color:#8B8172; font-style:normal; margin-top:.5em; }
.fm-quote{ margin:0 auto 2em; max-width:30em; text-align:center; font-style:italic; font-size:1em; color:#2C2822; line-height:1.7; }
/* contents */
.contents{ padding-top:2.5em; page-break-after:always; }
.contents h2{ text-align:center; font-size:1em; letter-spacing:.22em; text-transform:uppercase; font-weight:400; color:#2C2822; margin-bottom:2.6em; }
.toc{ max-width:34em; margin:0 auto; }
.toc-part{ margin:1.7em 0 .6em; font-size:.62em; letter-spacing:.24em; text-transform:uppercase; color:#A67C52; }
.toc-row{ display:flex; justify-content:space-between; align-items:baseline; padding:.32em 0; border-bottom:1px dotted rgba(166,124,82,.3); }
.toc-row .toc-num{ color:#8B8172; font-size:.72em; }
/* parts */
.part{ text-align:center; padding-top:4em; page-break-before:always; page-break-after:always; }
.part-num{ font-size:.62em; letter-spacing:.3em; text-transform:uppercase; color:#A67C52; }
.part h2{ font-size:1.6em; font-weight:400; color:#2C2822; margin:.9em 0 1.1em; line-height:1.2; }
.part-desc{ max-width:32em; margin:0 auto; color:#8B8172; font-style:italic; font-size:.9em; }
.part .epigraph{ margin-top:2.4em; font-style:italic; color:#2C2822; font-size:.95em; }
.part .motif{ margin-top:2.4em; color:#A67C52; font-size:.95em; letter-spacing:.5em; }
/* chapters */
.chapter{ page-break-before:always; }
.chapter-head{ text-align:center; margin-bottom:3.2em; }
.part-label{ font-size:.62em; letter-spacing:.26em; text-transform:uppercase; color:#8B8172; }
.chap-num{ display:block; margin-top:1.1em; font-size:.72em; letter-spacing:.34em; color:#A67C52; }
.chapter h3{ font-size:1.5em; font-weight:400; color:#2C2822; margin-top:.45em; line-height:1.22; }
.chapter .motif{ margin-top:1.5em; color:#C9A87C; font-size:.8em; letter-spacing:.5em; }
.chapter .rule{ width:56px; height:1px; background:#A67C52; margin:1.3em auto 0; opacity:.6; }
.chapter-body p{ margin-bottom:1.45em; text-align:justify; }
.chapter-body p.first::first-letter{ float:left; font-size:3.2em; line-height:.82; padding:.05em .12em 0 0; color:#2C2822; }
.chapter-body h4{ font-size:.68em; letter-spacing:.22em; text-transform:uppercase; color:#A67C52; margin:2.2em 0 .9em; font-weight:400; text-align:left; }
.scripture{ margin:1.8em 0 1.8em 1.4em; padding-left:1.3em; border-left:1px solid #C9A87C; font-style:italic; color:#403A31; }
.scripture p{ margin-bottom:.35em; text-align:left; }
.scripture cite{ display:block; font-style:normal; font-size:.62em; letter-spacing:.18em; text-transform:uppercase; color:#8B8172; margin-top:.45em; }
.pullquote{ margin:2.2em auto; max-width:26em; text-align:center; font-size:1.05em; font-style:italic; line-height:1.6; color:#2C2822; }
.pullquote::before,.pullquote::after{ content:''; display:block; width:24px; height:1px; background:#C9A87C; margin:1.1em auto; }
/* about / back */
.about{ padding-top:2.5em; page-break-before:always; }
.about h2{ text-align:center; font-size:1em; letter-spacing:.22em; text-transform:uppercase; font-weight:400; color:#2C2822; margin-bottom:2em; }
.about p{ max-width:36em; margin:0 auto 1.15em; text-align:justify; }
.back-cover{ padding-top:3em; text-align:center; page-break-before:always; }
.back-cover h2{ font-size:1em; letter-spacing:.22em; text-transform:uppercase; font-weight:400; color:#2C2822; margin-bottom:2em; }
.back-cover .big-line{ font-style:italic; font-size:1.15em; color:#2C2822; margin:1.6em 0; }
.back-cover p{ color:#403A31; margin:1.2em auto; max-width:34em; text-align:center; }
"""

# ---------------------------------------------------------------------------
# HTML / PDF
# ---------------------------------------------------------------------------
def memoir_html(include_cover=True, css=DIGITAL_CSS, cover_src=None):
    """Memoir HTML with cover page connected to the body."""
    d = bp.load_content()
    parts = []
    if include_cover:
        src = cover_src or os.path.join('..', '..', 'book_design', COVER)
        parts.append(f'<div class="cover-page"><img src="{src}" alt="Cover"></div>')
    parts.append(f'''<div class="title-page">
      <p class="kicker">A Journey Through the Many Faces of the Human Spirit</p>
      <h1>Renaissance<br><em>of the</em> Poor Soul</h1>
      <p class="sub">A journey through the many faces<br>of the human spirit</p>
      <p class="by">{bp.esc(AUTHOR)}</p>
    </div>''')
    parts.append(f'''<div class="copyright-page">
      <p style="letter-spacing:.06em">{bp.esc(TITLE)}</p>
      <p style="font-style:italic; margin-bottom:2em">A journey through the many faces of the human spirit<br>{bp.esc(AUTHOR)}</p>
      <p>Copyright &#169; 2026 {bp.esc(AUTHOR)}</p>
      <p style="margin-bottom:1.6em">All rights reserved.</p>
      <p class="lstext">No part of this book may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other non-commercial uses permitted by copyright law.</p>
      <p style="margin:1.2em 0 .3em"><strong>ISBN (Print): {ISBN_PRINT}</strong></p>
      <p style="margin:.3em 0"><strong>ISBN (Electronic): {ISBN_ELEC}</strong></p>
      <p>First published 2026</p>
      <p>Published in South Africa</p>
      <p style="font-size:.8em; margin-top:1.6em; color:#8B8172">Scripture quotations are from the Holy Bible and are used for spiritual reference and commentary.</p>
    </div>''')
    ded_paras = ''.join(f'<p>{bp.esc(p)}</p>' for p in d['dedication'].split('\n\n'))
    parts.append(f'''<div class="fm">
      <p class="fm-label">Dedication</p>
      <p class="ornament">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
      <div class="dedication-text">{ded_paras}</div>
    </div>''')
    fes = d['for_every_soul'].replace('\n', ' ')
    parts.append(f'''<div class="fm">
      <p class="fm-label">For Every Soul</p>
      <p class="ornament">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
      <div class="for-every-soul-text"><p>{bp.esc(fes)}</p></div>
    </div>''')
    pr = d['prayer']
    parts.append(f'''<div class="fm">
      <p class="fm-label">A Prayer</p>
      <p class="ornament">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
      <div class="prayer">
        <p class="zulu">{bp.esc(pr['zulu'])}</p>
        <p class="english">{bp.esc(pr['english'])}</p>
        <p class="attr">{bp.esc(pr['attr'])}</p>
      </div>
    </div>''')
    fw_html = ''.join(f'<p>{bp.inline(p)}</p>' for p in d['foreword'])
    parts.append(f'''<div class="fm">
      <p class="fm-label">Foreword</p>
      <p class="ornament">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
      <div class="fm-body">{fw_html}</div>
    </div>''')
    intro = d['introduction']
    intro_paras = ''.join(f'<p>{bp.inline(p)}</p>' for p in intro['paras'])
    parts.append(f'''<div class="fm">
      <p class="fm-label">Introduction</p>
      <p class="ornament">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
      <div class="fm-quote">{bp.esc(intro['quote'])}</div>
      <div class="fm-body">{intro_paras}</div>
    </div>''')
    toc_rows = []
    for part in d['toc']:
        toc_rows.append(f'<div class="toc-part">{bp.esc(part["part"])}</div>')
        for ch in part['chapters']:
            toc_rows.append(f'<div class="toc-row"><span>{bp.esc(ch["title"])}</span><span class="toc-num">{bp.esc(ch["num"])}</span></div>')
    toc_rows.append('<div class="toc-part">Back Matter</div>')
    toc_rows.append('<div class="toc-row"><span>About the Author</span><span class="toc-num">&#10022;</span></div>')
    parts.append(f'''<div class="contents">
      <h2>Contents</h2>
      <div class="toc">{''.join(toc_rows)}</div>
    </div>''')
    toc_parts = d['toc']
    for idx, part in enumerate(d['parts']):
        pnum = part['num']
        parts.append(f'''<div class="part">
          <p class="part-num">Part {bp.roman(pnum)}</p>
          <h2>{bp.esc(part['title'])}</h2>
          <p class="part-desc">{bp.esc(part.get('desc',''))}</p>
          <p class="epigraph">{bp.esc(part.get('epigraph',''))}</p>
          <p class="motif">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
        </div>''')
        toc_chapters = toc_parts[idx]['chapters'] if idx < len(toc_parts) else []
        toc_nums = {c['num'] for c in toc_chapters}
        for ch in d['chapters']:
            if ch['num'] in toc_nums:
                parts.append(bp.render_chapter(ch, part))
    about_html = ''.join(f'<p>{bp.inline(p)}</p>' for p in d['about'])
    parts.append(f'''<div class="about">
      <h2>About the Author</h2>
      {about_html}
    </div>''')
    bc = d['back_cover']
    bc_html = ''.join(f'<p>{bp.inline(p)}</p>' for p in bc)
    parts.append(f'''<div class="back-cover">
      <h2>Back Cover</h2>
      <p class="big-line">{bp.esc(bc[0])}</p>
      {bc_html}
    </div>''')
    body = '\n'.join(parts)
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{bp.esc(TITLE)}</title>
<style>{css}</style></head><body>
{body}
</body></html>'''

def build_html(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, 'book.html')
    with open(dst, 'w') as f:
        f.write(memoir_html(include_cover=True))
    return dst

def build_pdf(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, 'book.pdf')
    html_tmp = os.path.join(out_dir, '_book_tmp.html')
    with open(html_tmp, 'w') as f:
        f.write(memoir_html(include_cover=True, css=bp.PRINT_CSS))
    cmd = [CHROME, '--headless', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
           f'--print-to-pdf={dst}', 'file://' + html_tmp]
    r = subprocess.run(cmd, capture_output=True)
    os.remove(html_tmp)
    if r.returncode != 0:
        raise RuntimeError('chrome pdf failed: ' + r.stderr.decode()[:500])
    return dst

# ---------------------------------------------------------------------------
# Pandoc-based formats (EPUB, ODT, RTF, FB2)
# ---------------------------------------------------------------------------
def _pandoc(src_html, out_path, extra=None):
    """Run pandoc from the HTML's directory so relative cover paths resolve."""
    d = os.path.dirname(src_html)
    cmd = ['pandoc', os.path.basename(src_html), '-o', out_path]
    if extra:
        cmd += extra
    r = subprocess.run(cmd, cwd=d, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError('pandoc failed: ' + r.stderr.decode()[:800])
    return out_path

def build_epub(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, 'book.epub')
    html_tmp = os.path.join(out_dir, '_book_tmp.html')
    with open(html_tmp, 'w') as f:
        f.write(memoir_html(include_cover=True, css=EPUB_CSS))
    css_tmp = os.path.join(out_dir, '_book_tmp.css')
    with open(css_tmp, 'w') as f:
        f.write(EPUB_CSS)
    extra = ['--epub-cover-image=' + os.path.join(COVER_DIR, COVER),
             '--css=' + css_tmp,
             '--toc', '--toc-depth=2',
             '--metadata', f'title={TITLE}',
             '--metadata', f'author={AUTHOR}',
             '--metadata', f'lang=en',
             '--metadata', f'identifier={ISBN_ELEC}',
             '--metadata', f'publisher=Liviyo',
             '--metadata', 'date=2026']
    try:
        _pandoc(html_tmp, dst, extra)
    finally:
        os.remove(html_tmp)
        os.remove(css_tmp)
    return dst

def build_odt(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, 'book.odt')
    html_tmp = os.path.join(out_dir, '_book_tmp.html')
    with open(html_tmp, 'w') as f:
        f.write(memoir_html(include_cover=True, css=EPUB_CSS))
    try:
        _pandoc(html_tmp, dst)
    finally:
        os.remove(html_tmp)
    return dst

def build_rtf(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, 'book.rtf')
    html_tmp = os.path.join(out_dir, '_book_tmp.html')
    with open(html_tmp, 'w') as f:
        f.write(memoir_html(include_cover=True, css=EPUB_CSS))
    try:
        _pandoc(html_tmp, dst)
    finally:
        os.remove(html_tmp)
    return dst

def build_fb2(out_dir):
    import base64
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, 'book.fb2')
    d = bp.load_content()

    def esc_x(s):
        return html.escape(s).replace('"', '&quot;')

    def _strip(s):
        return re.sub(r'\*\*(.+?)\*\*', r'\1', s)

    body = []
    # front matter
    body.append('<section><title><p>Dedication</p></title>')
    for p in d['dedication'].split('\n\n'):
        body.append(f'<p>{esc_x(p.strip())}</p>')
    body.append('</section>')
    body.append('<section><title><p>For Every Soul</p></title>')
    body.append(f'<p>{esc_x(d["for_every_soul"].replace(chr(10), " "))}</p>')
    body.append('</section>')
    body.append('<section><title><p>A Prayer</p></title>')
    body.append(f'<p>{esc_x(d["prayer"]["zulu"])}</p>')
    body.append(f'<p>{esc_x(d["prayer"]["english"])}</p>')
    body.append(f'<p>{esc_x(d["prayer"]["attr"])}</p>')
    body.append('</section>')
    body.append('<section><title><p>Foreword</p></title>')
    for p in d['foreword']:
        body.append(f'<p>{esc_x(_strip(p))}</p>')
    body.append('</section>')
    body.append('<section><title><p>Introduction</p></title>')
    body.append(f'<p>{esc_x(d["introduction"]["quote"])}</p>')
    for p in d['introduction']['paras']:
        body.append(f'<p>{esc_x(_strip(p))}</p>')
    body.append('</section>')

    # parts + chapters
    toc_parts = d['toc']
    for idx, part in enumerate(d['parts']):
        body.append(f'<section><title><p>Part {bp.roman(part["num"])}: {esc_x(part["title"])}</p></title>')
        if part.get('desc'):
            body.append(f'<p>{esc_x(part["desc"])}</p>')
        if part.get('epigraph'):
            body.append(f'<p>{esc_x(part["epigraph"])}</p>')
        toc_chapters = toc_parts[idx]['chapters'] if idx < len(toc_parts) else []
        toc_nums = {c['num'] for c in toc_chapters}
        for ch in d['chapters']:
            if ch['num'] in toc_nums:
                body.append(f'<section><title><p>Chapter {esc_x(ch["num"])}: {esc_x(ch["title"])}</p></title>')
                for b in ch['body']:
                    t = b['type']
                    if t == 'p':
                        body.append(f'<p>{esc_x(_strip(b["text"]))}</p>')
                    elif t == 'h4':
                        body.append(f'<subtitle>{esc_x(b["text"])}</subtitle>')
                    elif t == 'scripture':
                        body.append(f'<poem><stanza><v>{esc_x(b["text"])}</v></stanza></poem>')
                        if b.get('cite'):
                            body.append(f'<p>{esc_x(b["cite"])}</p>')
                    elif t == 'pullquote':
                        body.append(f'<p>{esc_x(b["text"])}</p>')
                body.append('</section>')
        body.append('</section>')

    # about + back cover
    body.append('<section><title><p>About the Author</p></title>')
    for p in d['about']:
        body.append(f'<p>{esc_x(_strip(p))}</p>')
    body.append('</section>')
    body.append('<section><title><p>Back Cover</p></title>')
    for p in d['back_cover']:
        body.append(f'<p>{esc_x(_strip(p))}</p>')
    body.append('</section>')

    with open(os.path.join(COVER_DIR, COVER), 'rb') as f:
        cb = base64.b64encode(f.read()).decode()
    fb2 = f'''<?xml version="1.0" encoding="utf-8"?>
<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:l="http://www.w3.org/1999/xlink">
<description>
<title-info>
<genre>religion_spirit</genre>
<author><first-name>Halalisani</first-name><last-name>Ngema</last-name></author>
<book-title>{esc_x(TITLE)}</book-title>
<annotation><p>{esc_x(SUBTITLE)}</p></annotation>
<coverpage><image l:href="#cover.png"/></coverpage>
<lang>en</lang>
</title-info>
<document-info><author><first-name>Halalisani</first-name><last-name>Ngema</last-name></author>
<program-used>build_all_redesign</program-used><id>{ISBN_ELEC}</id><version>1.0</version></document-info>
<publish-info><isbn>{ISBN_ELEC}</isbn></publish-info>
</description>
<body>{''.join(body)}\n</body>
<binary id="cover.png" content-type="image/png">{cb}</binary>
</FictionBook>'''
    with open(dst, 'w') as f:
        f.write(fb2)
    return dst

# ---------------------------------------------------------------------------
# DOCX (python-docx, memoir-styled)
# ---------------------------------------------------------------------------
def build_docx(out_dir):
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor, Emu
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.section import WD_SECTION
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, 'book.docx')
    d = bp.load_content()

    INK = RGBColor(0x2C, 0x28, 0x22)
    BODY = RGBColor(0x40, 0x3A, 0x31)
    GOLD = RGBColor(0xA6, 0x7C, 0x52)
    MUTED = RGBColor(0x8B, 0x81, 0x72)
    FONT = 'EB Garamond'

    doc = Document()
    st = doc.styles['Normal']
    st.font.name = FONT
    st.font.size = Pt(11)
    st.font.color.rgb = BODY
    st.paragraph_format.line_spacing = 1.9

    def para(text='', align=WD_ALIGN_PARAGRAPH.LEFT, size=11, color=BODY,
             italic=False, bold=False, space_after=10, space_before=0):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.space_before = Pt(space_before)
        r = p.add_run(text)
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.color.rgb = color
        r.italic = italic
        r.bold = bold
        return p

    def page_break():
        doc.add_page_break()

    # --- cover image (page 1, connected to body) ---
    cover_path = os.path.join(COVER_DIR, COVER)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(cover_path, width=Inches(4.2))
    page_break()

    # --- title page ---
    para('A JOURNEY THROUGH THE MANY FACES OF THE HUMAN SPIRIT',
         WD_ALIGN_PARAGRAPH.CENTER, 9, GOLD, space_after=24)
    para('Renaissance of the Poor Soul', WD_ALIGN_PARAGRAPH.CENTER, 26, INK, space_after=12)
    para('A journey through the many faces of the human spirit',
         WD_ALIGN_PARAGRAPH.CENTER, 12, MUTED, italic=True, space_after=28)
    para('HALALISANI NGEMA', WD_ALIGN_PARAGRAPH.CENTER, 10, INK)
    page_break()

    # --- copyright ---
    para(TITLE, WD_ALIGN_PARAGRAPH.CENTER, 11, INK, space_after=6)
    para('A journey through the many faces of the human spirit', WD_ALIGN_PARAGRAPH.CENTER, 10, MUTED, italic=True, space_after=18)
    para('Copyright \u00a9 2026 Halalisani Ngema', WD_ALIGN_PARAGRAPH.CENTER, 10, BODY, space_after=4)
    para('All rights reserved.', WD_ALIGN_PARAGRAPH.CENTER, 10, BODY, space_after=14)
    para('No part of this book may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other non-commercial uses permitted by copyright law.',
         WD_ALIGN_PARAGRAPH.JUSTIFY, 9, MUTED, space_after=14)
    para('ISBN (Print): ' + ISBN_PRINT, WD_ALIGN_PARAGRAPH.CENTER, 10, BODY, space_after=2)
    para('ISBN (Electronic): ' + ISBN_ELEC, WD_ALIGN_PARAGRAPH.CENTER, 10, BODY, space_after=10)
    para('First published 2026', WD_ALIGN_PARAGRAPH.CENTER, 10, BODY, space_after=2)
    para('Published in South Africa', WD_ALIGN_PARAGRAPH.CENTER, 10, BODY)
    page_break()

    # --- front matter ---
    def fm_label(text):
        para(text, WD_ALIGN_PARAGRAPH.CENTER, 9, GOLD, space_after=18)
        para('\u2722   \u2722   \u2722', WD_ALIGN_PARAGRAPH.CENTER, 11, RGBColor(0xC9, 0xA8, 0x7C), space_after=18)

    fm_label('DEDICATION')
    for ptext in d['dedication'].split('\n\n'):
        para(ptext.strip(), WD_ALIGN_PARAGRAPH.CENTER, 12, BODY, italic=True, space_after=12)
    page_break()

    fm_label('FOR EVERY SOUL')
    para(d['for_every_soul'].replace('\n', ' '), WD_ALIGN_PARAGRAPH.CENTER, 12, BODY, italic=True)
    page_break()

    fm_label('A PRAYER')
    para(d['prayer']['zulu'], WD_ALIGN_PARAGRAPH.CENTER, 14, INK, italic=True, space_after=12)
    para(d['prayer']['english'], WD_ALIGN_PARAGRAPH.CENTER, 10, MUTED, space_after=14)
    para(d['prayer']['attr'], WD_ALIGN_PARAGRAPH.CENTER, 9, GOLD)
    page_break()

    fm_label('FOREWORD')
    for ptext in d['foreword']:
        t = re.sub(r'\*\*(.+?)\*\*', r'\1', ptext)
        para(t, WD_ALIGN_PARAGRAPH.JUSTIFY, 11, BODY, space_after=12)
    page_break()

    fm_label('INTRODUCTION')
    para(d['introduction']['quote'], WD_ALIGN_PARAGRAPH.CENTER, 12, INK, italic=True, space_after=18)
    for ptext in d['introduction']['paras']:
        t = re.sub(r'\*\*(.+?)\*\*', r'\1', ptext)
        para(t, WD_ALIGN_PARAGRAPH.JUSTIFY, 11, BODY, space_after=12)
    page_break()

    # --- contents ---
    para('CONTENTS', WD_ALIGN_PARAGRAPH.CENTER, 12, INK, space_after=24)
    for part in d['toc']:
        para(part['part'], WD_ALIGN_PARAGRAPH.LEFT, 9, GOLD, space_before=14, space_after=6)
        for ch in part['chapters']:
            para(f"{ch['title']}  \u2014  {ch['num']}", WD_ALIGN_PARAGRAPH.LEFT, 10, BODY, space_after=4)
    para('BACK MATTER', WD_ALIGN_PARAGRAPH.LEFT, 9, GOLD, space_before=14, space_after=6)
    para('About the Author', WD_ALIGN_PARAGRAPH.LEFT, 10, BODY, space_after=4)
    page_break()

    # --- parts + chapters ---
    toc_parts = d['toc']
    for idx, part in enumerate(d['parts']):
        para(f"PART {bp.roman(part['num'])}", WD_ALIGN_PARAGRAPH.CENTER, 9, GOLD, space_before=60, space_after=10)
        para(part['title'], WD_ALIGN_PARAGRAPH.CENTER, 22, INK, space_after=14)
        if part.get('desc'):
            para(part['desc'], WD_ALIGN_PARAGRAPH.CENTER, 11, MUTED, italic=True, space_after=14)
        if part.get('epigraph'):
            para(part['epigraph'], WD_ALIGN_PARAGRAPH.CENTER, 12, INK, italic=True, space_after=14)
        para('\u2722   \u2722   \u2722', WD_ALIGN_PARAGRAPH.CENTER, 11, RGBColor(0xC9, 0xA8, 0x7C), space_after=20)
        page_break()
        toc_chapters = toc_parts[idx]['chapters'] if idx < len(toc_parts) else []
        toc_nums = {c['num'] for c in toc_chapters}
        for ch in d['chapters']:
            if ch['num'] in toc_nums:
                para(part['title'], WD_ALIGN_PARAGRAPH.CENTER, 8, MUTED, space_after=8)
                para(f"CHAPTER {ch['num']}", WD_ALIGN_PARAGRAPH.CENTER, 9, GOLD, space_after=8)
                para(ch['title'], WD_ALIGN_PARAGRAPH.CENTER, 18, INK, space_after=10)
                para('\u2722   \u2722', WD_ALIGN_PARAGRAPH.CENTER, 10, RGBColor(0xC9, 0xA8, 0x7C), space_after=16)
                first = True
                for b in ch['body']:
                    t = b['type']
                    if t == 'p':
                        txt = re.sub(r'\*\*(.+?)\*\*', r'\1', b['text'])
                        para(txt, WD_ALIGN_PARAGRAPH.JUSTIFY, 11, BODY, space_after=12)
                        first = False
                    elif t == 'h4':
                        para(b['text'], WD_ALIGN_PARAGRAPH.LEFT, 9, GOLD, space_before=16, space_after=8)
                    elif t == 'scripture':
                        para(b['text'], WD_ALIGN_PARAGRAPH.LEFT, 11, BODY, italic=True, space_after=4)
                        if b.get('cite'):
                            para(b['cite'], WD_ALIGN_PARAGRAPH.LEFT, 8, MUTED, space_after=12)
                    elif t == 'pullquote':
                        para(b['text'], WD_ALIGN_PARAGRAPH.CENTER, 13, INK, italic=True, space_before=16, space_after=16)
                page_break()

    # --- about ---
    para('ABOUT THE AUTHOR', WD_ALIGN_PARAGRAPH.CENTER, 12, INK, space_after=20)
    for ptext in d['about']:
        t = re.sub(r'\*\*(.+?)\*\*', r'\1', ptext)
        para(t, WD_ALIGN_PARAGRAPH.JUSTIFY, 11, BODY, space_after=12)
    page_break()

    # --- back cover ---
    para('BACK COVER', WD_ALIGN_PARAGRAPH.CENTER, 12, INK, space_after=20)
    bc = d['back_cover']
    para(bc[0], WD_ALIGN_PARAGRAPH.CENTER, 14, INK, italic=True, space_after=14)
    for ptext in bc[1:]:
        t = re.sub(r'\*\*(.+?)\*\*', r'\1', ptext)
        para(t, WD_ALIGN_PARAGRAPH.CENTER, 11, BODY, space_after=12)

    doc.save(dst)
    return dst

# ---------------------------------------------------------------------------
# Markdown / TXT (from JSON)
# ---------------------------------------------------------------------------
def build_markdown(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, 'book.md')
    d = bp.load_content()
    out = []
    out.append(f'# {d["title"]}')
    out.append('')
    out.append(f'*{d["subtitle"].replace(chr(10), " ")}*')
    out.append('')
    out.append(f'**{AUTHOR}**')
    out.append('')
    out.append('---')
    out.append('')
    out.append('## Dedication')
    out.append('')
    for p in d['dedication'].split('\n\n'):
        out.append(p.strip())
        out.append('')
    out.append('## For Every Soul')
    out.append('')
    out.append(d['for_every_soul'].replace('\n', ' '))
    out.append('')
    out.append('## A Prayer')
    out.append('')
    out.append(f'*{d["prayer"]["zulu"]}*')
    out.append('')
    out.append(d['prayer']['english'])
    out.append('')
    out.append(f'*{d["prayer"]["attr"]}*')
    out.append('')
    out.append('## Foreword')
    out.append('')
    for p in d['foreword']:
        out.append(p)
        out.append('')
    out.append('## Introduction')
    out.append('')
    out.append(f'> {d["introduction"]["quote"]}')
    out.append('')
    for p in d['introduction']['paras']:
        out.append(p)
        out.append('')
    out.append('## Contents')
    out.append('')
    for part in d['toc']:
        out.append(f'### {part["part"]}')
        out.append('')
        for ch in part['chapters']:
            out.append(f'- {ch["title"]} ({ch["num"]})')
        out.append('')
    out.append('---')
    out.append('')
    toc_parts = d['toc']
    for idx, part in enumerate(d['parts']):
        out.append(f'# PART {bp.roman(part["num"])}: {part["title"]}')
        out.append('')
        if part.get('desc'):
            out.append(f'*{part["desc"]}*')
            out.append('')
        if part.get('epigraph'):
            out.append(f'> {part["epigraph"]}')
            out.append('')
        toc_chapters = toc_parts[idx]['chapters'] if idx < len(toc_parts) else []
        toc_nums = {c['num'] for c in toc_chapters}
        for ch in d['chapters']:
            if ch['num'] in toc_nums:
                out.append(f'## Chapter {ch["num"]}: {ch["title"]}')
                out.append('')
                for b in ch['body']:
                    t = b['type']
                    if t == 'p':
                        out.append(b['text'])
                        out.append('')
                    elif t == 'h4':
                        out.append(f'#### {b["text"]}')
                        out.append('')
                    elif t == 'scripture':
                        out.append(f'> {b["text"]}')
                        if b.get('cite'):
                            out.append(f'> — {b["cite"]}')
                        out.append('')
                    elif t == 'pullquote':
                        out.append(f'*{b["text"]}*')
                        out.append('')
    out.append('---')
    out.append('')
    out.append('## About the Author')
    out.append('')
    for p in d['about']:
        out.append(p)
        out.append('')
    out.append('## Back Cover')
    out.append('')
    for p in d['back_cover']:
        out.append(p)
        out.append('')
    with open(dst, 'w') as f:
        f.write('\n'.join(out))
    return dst

def build_txt(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, 'book.txt')
    d = bp.load_content()
    out = []
    out.append(d['title'])
    out.append('=' * min(len(d['title']), 60))
    out.append('')
    out.append(d['subtitle'].replace('\n', ' '))
    out.append('')
    out.append(f'by {AUTHOR}')
    out.append('')
    out.append('* * *')
    out.append('')
    out.append('DEDICATION')
    out.append('')
    for p in d['dedication'].split('\n\n'):
        out.append(p.strip())
        out.append('')
    out.append('FOR EVERY SOUL')
    out.append('')
    out.append(d['for_every_soul'].replace('\n', ' '))
    out.append('')
    out.append('A PRAYER')
    out.append('')
    out.append(d['prayer']['zulu'])
    out.append('')
    out.append(d['prayer']['english'])
    out.append('')
    out.append(d['prayer']['attr'])
    out.append('')
    out.append('FOREWORD')
    out.append('')
    for p in d['foreword']:
        out.append(re.sub(r'\*\*(.+?)\*\*', r'\1', p))
        out.append('')
    out.append('INTRODUCTION')
    out.append('')
    out.append(d['introduction']['quote'])
    out.append('')
    for p in d['introduction']['paras']:
        out.append(re.sub(r'\*\*(.+?)\*\*', r'\1', p))
        out.append('')
    out.append('CONTENTS')
    out.append('')
    for part in d['toc']:
        out.append(part['part'])
        for ch in part['chapters']:
            out.append(f"  {ch['title']} ({ch['num']})")
        out.append('')
    out.append('* * *')
    out.append('')
    toc_parts = d['toc']
    for idx, part in enumerate(d['parts']):
        out.append(f"PART {bp.roman(part['num'])}: {part['title']}".upper())
        out.append('')
        if part.get('desc'):
            out.append(part['desc'])
            out.append('')
        if part.get('epigraph'):
            out.append(part['epigraph'])
            out.append('')
        toc_chapters = toc_parts[idx]['chapters'] if idx < len(toc_parts) else []
        toc_nums = {c['num'] for c in toc_chapters}
        for ch in d['chapters']:
            if ch['num'] in toc_nums:
                out.append(f"CHAPTER {ch['num']}: {ch['title']}".upper())
                out.append('')
                for b in ch['body']:
                    t = b['type']
                    if t == 'p':
                        out.append(re.sub(r'\*\*(.+?)\*\*', r'\1', b['text']))
                        out.append('')
                    elif t == 'h4':
                        out.append(b['text'].upper())
                        out.append('')
                    elif t == 'scripture':
                        out.append(b['text'])
                        if b.get('cite'):
                            out.append(f"— {b['cite']}")
                        out.append('')
                    elif t == 'pullquote':
                        out.append(b['text'])
                        out.append('')
    out.append('* * *')
    out.append('')
    out.append('ABOUT THE AUTHOR')
    out.append('')
    for p in d['about']:
        out.append(re.sub(r'\*\*(.+?)\*\*', r'\1', p))
        out.append('')
    out.append('BACK COVER')
    out.append('')
    for p in d['back_cover']:
        out.append(re.sub(r'\*\*(.+?)\*\*', r'\1', p))
        out.append('')
    with open(dst, 'w') as f:
        f.write('\n'.join(out))
    return dst

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
BUILDERS = [
    ('HTML', build_html),
    ('PDF', build_pdf),
    ('EPUB', build_epub),
    ('DOCX', build_docx),
    ('ODT', build_odt),
    ('RTF', build_rtf),
    ('FB2', build_fb2),
    ('Markdown', build_markdown),
    ('TXT', build_txt),
]

def main():
    results = {}
    for fmt, fn in BUILDERS:
        out_dir = os.path.join(BOOK_FORMATS, fmt)
        try:
            p = fn(out_dir)
            results[fmt] = p
            print(f"{fmt:10s} OK  {os.path.basename(p)} ({os.path.getsize(p)} B)")
        except Exception as e:
            results[fmt] = None
            print(f"{fmt:10s} ERROR {e}")
    # copy to root-level dirs (identical duplicates)
    print("\n--- copying to root-level format dirs ---")
    for fmt, src in results.items():
        if src is None:
            continue
        dst_dir = os.path.join(ROOT, fmt)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, os.path.basename(src))
        shutil.copy2(src, dst)
        print(f"  {fmt:10s} -> {dst}")

if __name__ == '__main__':
    main()