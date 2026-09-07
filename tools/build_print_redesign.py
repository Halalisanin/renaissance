#!/usr/bin/env python3
"""Redesigned PRINT interior generator (memoir design).

Renders the approved memoir design (from book.html) as an A5 print interior
for each of the five cover variations, writing to:

    book_formats/print/coverX/book/interior.html
    book_formats/print/coverX/book/interior.pdf

Content is sourced from the structured redesign JSON (scripture/pullquote
classification already applied). Page count targets ~97 A5 pages.
"""
import os, re, html, json, subprocess, argparse

ROOT = '/home/win/liviyo_pc/job/websites/liviyo_capital/working_sites/jobs_renaissance/Renaissance_of_the_Poor_Soul'
CONTENT_JSON = '/tmp/opencode/book_content_final.json'
OUT_BASE = os.path.join(ROOT, 'book_formats', 'print')
CHROME = '/home/win/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'

ISBN_PRINT = '978-1-0492-8328-9'
TITLE = 'Renaissance of the Poor Soul'
AUTHOR = 'Halalisani Ngema'
COVERS = ['cover1.png', 'cover2.png', 'cover3.png', 'cover4.png', 'cover5.png']

def esc(x):
    return html.escape(x, quote=False)

def inline(s):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', esc(s))

PRINT_CSS = """
@page{
  size: 148mm 210mm;
  margin: 16mm 17mm 16mm 17mm;
  @bottom-center{ content: counter(page); font-family:'EB Garamond',Georgia,serif;
    font-size:8.5pt; color:#8B8172; letter-spacing:.08em; }
}
@page:first{ margin:0; @bottom-center{ content: none; } }
*{ box-sizing:border-box; margin:0; padding:0; }
html,body{ margin:0; padding:0; }
body{
  font-family:'EB Garamond',Georgia,'Times New Roman',serif;
  background:#FBF8F1; color:#403A31;
  font-size:13pt; line-height:2.0;
  -webkit-print-color-adjust:exact; print-color-adjust:exact;
}
/* ===== cover page (full bleed) ===== */
.cover-page{ page-break-after:always; position:relative; width:148mm; height:210mm; overflow:hidden; }
.cover-page img{ position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; display:block; }
/* ===== title page ===== */
.title-page{ page-break-after:always; text-align:center; padding-top:62mm; }
.title-page .kicker{ font-size:8pt; letter-spacing:.3em; text-transform:uppercase; color:#A67C52; margin-bottom:2.2em; }
.title-page h1{ font-family:'EB Garamond',Georgia,serif; font-size:27pt; font-weight:400; color:#2C2822; line-height:1.14; letter-spacing:.01em; margin:0 0 .5em; }
.title-page h1 em{ font-style:italic; color:#A67C52; }
.title-page .sub{ font-style:italic; font-size:12.5pt; color:#8B8172; margin:0 0 2.8em; line-height:1.5; }
.title-page .by{ letter-spacing:.26em; text-transform:uppercase; font-size:9pt; color:#2C2822; }
/* ===== copyright ===== */
.copyright-page{ page-break-after:always; padding-top:50mm; text-align:center; font-size:9pt; color:#403A31; line-height:1.75; }
.copyright-page .lstext{ text-align:justify; font-size:8.2pt; margin:1.6em 2em; color:#8B8172; }
.copyright-page strong{ color:#2C2822; }
/* ===== front matter ===== */
.fm{ page-break-after:always; text-align:center; padding-top:38mm; }
.fm-label{ font-size:7.5pt; letter-spacing:.28em; text-transform:uppercase; color:#A67C52; margin-bottom:2.2em; }
.ornament{ color:#C9A87C; font-size:11pt; margin-bottom:1.8em; letter-spacing:.4em; }
.dedication-text{ font-style:italic; font-size:12pt; color:#403A31; max-width:34em; margin:0 auto; line-height:2; }
.for-every-soul-text{ font-style:italic; font-size:12pt; color:#403A31; max-width:30em; margin:0 auto; line-height:2; }
.prayer .zulu{ font-size:15pt; font-style:italic; color:#2C2822; }
.prayer .english{ color:#8B8172; margin-top:1.1em; font-size:11pt; }
.prayer .attr{ font-size:7.5pt; letter-spacing:.2em; text-transform:uppercase; color:#A67C52; margin-top:1.6em; }
.fm-body{ text-align:left; max-width:36em; margin:0 auto; }
.fm-body p{ margin-bottom:1.15em; text-align:justify; }
.fm-body .signoff{ margin-top:2em; font-style:italic; color:#A67C52; text-align:right; }
.fm-body .signoff .place{ display:block; font-size:7.5pt; letter-spacing:.2em; text-transform:uppercase; color:#8B8172; font-style:normal; margin-top:.5em; }
.fm-quote{ margin:0 auto 2em; max-width:30em; text-align:center; font-style:italic; font-size:12.5pt; color:#2C2822; line-height:1.7; }
/* ===== contents ===== */
.contents{ page-break-after:always; padding-top:30mm; }
.contents h2{ text-align:center; font-size:13pt; letter-spacing:.22em; text-transform:uppercase; font-weight:400; color:#2C2822; margin-bottom:2.6em; }
.toc{ max-width:34em; margin:0 auto; }
.toc-part{ margin:1.7em 0 .6em; font-size:7.5pt; letter-spacing:.24em; text-transform:uppercase; color:#A67C52; }
.toc-row{ display:flex; justify-content:space-between; align-items:baseline; padding:.32em 0; border-bottom:1px dotted rgba(166,124,82,.3); }
.toc-row .toc-num{ color:#8B8172; font-size:9pt; }
/* ===== parts ===== */
.part{ page-break-before:always; page-break-after:always; text-align:center; padding-top:56mm; }
.part-num{ font-size:8pt; letter-spacing:.3em; text-transform:uppercase; color:#A67C52; }
.part h2{ font-size:22pt; font-weight:400; color:#2C2822; margin:.9em 0 1.1em; line-height:1.2; }
.part-desc{ max-width:32em; margin:0 auto; color:#8B8172; font-style:italic; font-size:11.5pt; }
.part .epigraph{ margin-top:2.4em; font-style:italic; color:#2C2822; font-size:12pt; }
.part .motif{ margin-top:2.4em; color:#A67C52; font-size:12pt; letter-spacing:.5em; }
/* ===== chapters ===== */
.chapter{ page-break-before:always; }
.chapter-head{ text-align:center; margin-bottom:3.2em; }
.part-label{ font-size:7.5pt; letter-spacing:.26em; text-transform:uppercase; color:#8B8172; }
.chap-num{ display:block; margin-top:1.1em; font-size:9pt; letter-spacing:.34em; color:#A67C52; }
.chapter h3{ font-size:20pt; font-weight:400; color:#2C2822; margin-top:.45em; line-height:1.22; }
.chapter .motif{ margin-top:1.5em; color:#C9A87C; font-size:10pt; letter-spacing:.5em; }
.chapter .rule{ width:56px; height:1px; background:#A67C52; margin:1.3em auto 0; opacity:.6; }
.chapter-body p{ margin-bottom:1.45em; text-align:justify; }
.chapter-body p.first::first-letter{
  float:left; font-size:3.2em; line-height:.82;
  padding:.05em .12em 0 0; color:#2C2822;
}
.chapter-body h4{
  font-size:8.5pt; letter-spacing:.22em; text-transform:uppercase;
  color:#A67C52; margin:2.2em 0 .9em; font-weight:400; text-align:left;
}
.scripture{
  margin:1.8em 0 1.8em 1.4em; padding-left:1.3em;
  border-left:1px solid #C9A87C;
  font-style:italic; color:#403A31;
}
.scripture p{ margin-bottom:.35em; text-align:left; }
.scripture cite{ display:block; font-style:normal; font-size:7.5pt; letter-spacing:.18em; text-transform:uppercase; color:#8B8172; margin-top:.45em; }
.pullquote{
  margin:2.2em auto; max-width:26em; text-align:center;
  font-size:13.5pt; font-style:italic; line-height:1.6; color:#2C2822;
}
.pullquote::before,.pullquote::after{
  content:''; display:block; width:24px; height:1px;
  background:#C9A87C; margin:1.1em auto;
}
/* ===== about / back ===== */
.about{ page-break-before:always; padding-top:30mm; }
.about h2{ text-align:center; font-size:13pt; letter-spacing:.22em; text-transform:uppercase; font-weight:400; color:#2C2822; margin-bottom:2em; }
.about p{ max-width:36em; margin:0 auto 1.15em; text-align:justify; }
.back-cover{ page-break-before:always; padding-top:34mm; text-align:center; }
.back-cover h2{ font-size:13pt; letter-spacing:.22em; text-transform:uppercase; font-weight:400; color:#2C2822; margin-bottom:2em; }
.back-cover .big-line{ font-style:italic; font-size:15pt; color:#2C2822; margin:1.6em 0; }
.back-cover p{ color:#403A31; margin:1.2em auto; max-width:34em; text-align:center; }
"""

def load_content():
    with open(CONTENT_JSON) as f:
        return json.load(f)

def render_html(cfile, cover_rel, include_cover=True):
    d = load_content()
    parts = []

    # --- front matter ---
    if include_cover:
        parts.append(f'''<div class="cover-page"><img src="{cover_rel}{esc(cfile)}" alt="Cover"></div>''')

    parts.append(f'''<div class="title-page">
      <p class="kicker">A Journey Through the Many Faces of the Human Spirit</p>
      <h1>Renaissance<br><em>of the</em> Poor Soul</h1>
      <p class="sub">A journey through the many faces<br>of the human spirit</p>
      <p class="by">{esc(AUTHOR)}</p>
    </div>''')

    parts.append(f'''<div class="copyright-page">
      <p style="letter-spacing:.06em">{esc(TITLE)}</p>
      <p style="font-style:italic; margin-bottom:2em">A journey through the many faces of the human spirit<br>{esc(AUTHOR)}</p>
      <p>Copyright &#169; 2026 {esc(AUTHOR)}</p>
      <p style="margin-bottom:1.6em">All rights reserved.</p>
      <p class="lstext">No part of this book may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other non-commercial uses permitted by copyright law.</p>
      <p style="margin:1.2em 0 .3em"><strong>ISBN (Print): {ISBN_PRINT}</strong></p>
      <p>First published 2026</p>
      <p>Published in South Africa</p>
      <p style="font-size:8pt; margin-top:1.6em; color:#8B8172">Scripture quotations are from the Holy Bible and are used for spiritual reference and commentary.</p>
    </div>''')

    # dedication
    ded_paras = ''.join(f'<p>{esc(p)}</p>' for p in d['dedication'].split('\n\n'))
    parts.append(f'''<div class="fm">
      <p class="fm-label">Dedication</p>
      <p class="ornament">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
      <div class="dedication-text">{ded_paras}</div>
    </div>''')

    # for every soul
    fes = d['for_every_soul'].replace('\n', ' ')
    parts.append(f'''<div class="fm">
      <p class="fm-label">For Every Soul</p>
      <p class="ornament">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
      <div class="for-every-soul-text"><p>{esc(fes)}</p></div>
    </div>''')

    # prayer
    pr = d['prayer']
    parts.append(f'''<div class="fm">
      <p class="fm-label">A Prayer</p>
      <p class="ornament">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
      <div class="prayer">
        <p class="zulu">{esc(pr['zulu'])}</p>
        <p class="english">{esc(pr['english'])}</p>
        <p class="attr">{esc(pr['attr'])}</p>
      </div>
    </div>''')

    # foreword
    fw = d['foreword']
    fw_html = ''.join(f'<p>{inline(p)}</p>' for p in fw)
    parts.append(f'''<div class="fm">
      <p class="fm-label">Foreword</p>
      <p class="ornament">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
      <div class="fm-body">{fw_html}</div>
    </div>''')

    # introduction
    intro = d['introduction']
    intro_paras = ''.join(f'<p>{inline(p)}</p>' for p in intro['paras'])
    parts.append(f'''<div class="fm">
      <p class="fm-label">Introduction</p>
      <p class="ornament">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
      <div class="fm-quote">{esc(intro['quote'])}</div>
      <div class="fm-body">{intro_paras}</div>
    </div>''')

    # contents
    toc_rows = []
    for part in d['toc']:
        toc_rows.append(f'<div class="toc-part">{esc(part["part"])}</div>')
        for ch in part['chapters']:
            toc_rows.append(f'<div class="toc-row"><span>{esc(ch["title"])}</span><span class="toc-num">{esc(ch["num"])}</span></div>')
    toc_rows.append('<div class="toc-part">Back Matter</div>')
    toc_rows.append('<div class="toc-row"><span>About the Author</span><span class="toc-num">&#10022;</span></div>')
    parts.append(f'''<div class="contents">
      <h2>Contents</h2>
      <div class="toc">{''.join(toc_rows)}</div>
    </div>''')

    # --- parts + chapters (mapping from TOC) ---
    toc_parts = d['toc']
    for idx, part in enumerate(d['parts']):
        pnum = part['num']
        parts.append(f'''<div class="part">
          <p class="part-num">Part {roman(pnum)}</p>
          <h2>{esc(part['title'])}</h2>
          <p class="part-desc">{esc(part.get('desc',''))}</p>
          <p class="epigraph">{esc(part.get('epigraph',''))}</p>
          <p class="motif">&#10022; &nbsp; &#10022; &nbsp; &#10022;</p>
        </div>''')
        toc_chapters = toc_parts[idx]['chapters'] if idx < len(toc_parts) else []
        toc_nums = {c['num'] for c in toc_chapters}
        for ch in d['chapters']:
            if ch['num'] in toc_nums:
                parts.append(render_chapter(ch, part))

    # about
    about_html = ''.join(f'<p>{inline(p)}</p>' for p in d['about'])
    parts.append(f'''<div class="about">
      <h2>About the Author</h2>
      {about_html}
    </div>''')

    # back cover
    bc = d['back_cover']
    bc_html = ''.join(f'<p>{inline(p)}</p>' for p in bc)
    parts.append(f'''<div class="back-cover">
      <h2>Back Cover</h2>
      <p class="big-line">{esc(bc[0])}</p>
      {bc_html}
    </div>''')

    body = '\n'.join(parts)
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{esc(TITLE)}</title>
<style>{PRINT_CSS}</style></head><body>
{body}
</body></html>'''

def roman(num):
    words = {'ONE':1,'TWO':2,'THREE':3,'FOUR':4,'FIVE':5,'SIX':6,'SEVEN':7,'EIGHT':8,'NINE':9,'TEN':10}
    if isinstance(num, str) and not num.isdigit():
        num = words.get(num.strip().upper(), 1)
    n = int(num)
    vals = [(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    out = ''
    for v,s in vals:
        while n >= v:
            out += s; n -= v
    return out

def render_chapter(ch, part):
    head = f'''<div class="chapter-head">
      <span class="part-label">{esc(part['title'])}</span>
      <span class="chap-num">CHAPTER {esc(ch['num'])}</span>
      <h3>{esc(ch['title'])}</h3>
      <p class="motif">&#10022; &nbsp; &#10022;</p>
      <div class="rule"></div>
    </div>'''
    body_blocks = []
    first = True
    for b in ch['body']:
        t = b['type']
        if t == 'p':
            cls = ' class="first"' if first else ''
            first = False
            body_blocks.append(f'<p{cls}>{inline(b["text"])}</p>')
        elif t == 'h4':
            body_blocks.append(f'<h4>{esc(b["text"])}</h4>')
        elif t == 'scripture':
            body_blocks.append(f'<div class="scripture"><p>{esc(b["text"])}</p><cite>{esc(b.get("cite",""))}</cite></div>')
        elif t == 'pullquote':
            body_blocks.append(f'<div class="pullquote">{esc(b["text"])}</div>')
    return f'''<div class="chapter">
      {head}
      <div class="chapter-body">{''.join(body_blocks)}</div>
    </div>'''

def build(cid, cfile, include_cover=True, out_base=OUT_BASE):
    d = os.path.join(out_base, cid, 'book')
    os.makedirs(d, exist_ok=True)
    cover_rel = '../../../../book_design/'
    html_path = os.path.join(d, 'interior.html')
    with open(html_path, 'w') as f:
        f.write(render_html(cfile, cover_rel, include_cover))
    pdf_path = os.path.join(d, 'interior.pdf')
    cmd = [CHROME, '--headless', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
           f'--print-to-pdf={pdf_path}', 'file://' + html_path]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[:500])
    return html_path, pdf_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-cover', action='store_true', help='omit the full-bleed cover page')
    ap.add_argument('--out-base', default=OUT_BASE, help='output base directory (default: book_formats/print)')
    args = ap.parse_args()
    os.makedirs(args.out_base, exist_ok=True)
    for i, cfile in enumerate(COVERS):
        cid = f'cover{i+1}'
        h, p = build(cid, cfile, include_cover=not args.no_cover, out_base=args.out_base)
        print(f"{cid}: interior.pdf {os.path.getsize(p)} B")

if __name__ == '__main__':
    main()