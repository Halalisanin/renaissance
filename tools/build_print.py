#!/usr/bin/env python3
"""Print-ready INTERIOR generation for each cover.

Creates print/coverX/book/interior.html and renders interior.pdf via headless
Chrome at an A5 trim (148 x 210 mm). Includes full-bleed cover page,
title page, copyright page carrying the PRINT ISBN, contents, manuscript with
chapter/part page breaks, about the author, and back cover. Print ISBN is
placed on the copyright page as required.
"""
import os, re, html, subprocess

ROOT = '/home/win/liviyo_pc/job/websites/liviyo_capital/working_sites/jobs_renaissance/Renaissance_of_the_Poor_Soul'
MD_SRC = os.path.join(ROOT, 'source', 'book.md')
COVER_DIR = os.path.join(ROOT, 'book_design')
PRINT = os.path.join(ROOT, 'print')
CHROME = '/home/win/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'

ISBN_PRINT = '978-1-0492-8328-9'
TITLE = 'Renaissance of the Poor Soul'
SUBTITLE = 'A journey through the many faces of the human spirit'
AUTHOR = 'Halalisani Ngema'
TRIM_W_MM, TRIM_H_MM = 148, 210   # A5

COVERS = ['cover1.png','cover2.png','cover3.png','cover4.png','cover5.png']

def parse_blocks():
    with open(MD_SRC) as f:
        raw=f.read()
    blocks=[]
    for ln in raw.split('\n'):
        s=ln.strip()
        if not s or s=='---': continue
        if s.startswith('# ') and not s.startswith('## '):
            blocks.append(('h1',s[2:].strip()))
        elif s.startswith('## '):
            blocks.append(('h2',s[3:].strip()))
        elif s=='* * *':
            blocks.append(('orn',None))
        elif s.startswith('> '):
            blocks.append(('verse',s[2:].strip()))
        elif s.startswith('*') and s.endswith('*') and len(s)<80 and s.count('*')<=2:
            blocks.append(('em',s.strip('*')))
        else:
            blocks.append(('p',s))
    return blocks

def esc(x): return html.escape(x, quote=False)
def inline(s): return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',esc(s))
def scripture(s):
    return s.startswith('"') and ' - ' in s and s.rstrip().endswith('"')

PRINT_CSS = """
@page{ size: 148mm 210mm; margin: 17mm 18mm 15mm 18mm; }
@page:first{ margin:0; }
*{ box-sizing:border-box; }
html,body{ margin:0; padding:0; }
body{ font-family: Georgia, 'Palatino Linotype', 'Times New Roman', serif;
  color:#1a1a17; background:#fff; font-size:10pt; line-height:1.58; }
.cover-page{ page-break-after:always; position:relative; width:148mm; height:210mm; overflow:hidden; }
.cover-page img{ position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; display:block; }
.page-break{ page-break-before:always; }
.title-page{ text-align:center; padding-top:60mm; }
.title-page h1{ font-size:26pt; font-weight:400; letter-spacing:.02em; margin:0 0 .6em; line-height:1.12; }
.title-page .sub{ font-style:italic; font-size:13pt; margin:0 0 2.6em; color:#444; }
.title-page .by{ letter-spacing:.24em; text-transform:uppercase; font-size:10pt; }
.copyright-page{ padding-top:52mm; text-align:center; font-size:9pt; color:#333; line-height:1.7; }
.copyright-page .lstext{ text-align:justify; font-size:8.4pt; margin:1.4em 2em; color:#444; }
.copyright-page strong{ color:#111; }
.fm h2{ text-align:center; font-size:13pt; letter-spacing:.1em; text-transform:uppercase; font-weight:400; margin:0 0 1.4em; }
.fm p{ text-align:justify; text-indent:1.3em; margin:0 0 .75em; }
.fm .sign{ text-align:right; text-indent:0; font-style:italic; }
h2.part{ page-break-before:always; text-align:center; font-size:16pt; letter-spacing:.24em;
  text-transform:uppercase; font-weight:400; margin-top:40mm; }
h3.chapter{ page-break-before:always; text-align:center; font-size:14pt; font-weight:400;
  letter-spacing:.05em; margin:2.4em 0 1.2em; }
h3.chapter::before{ content:""; display:block; width:34px; height:1px; background:#9a7b3f; margin:0 auto 1.1em; }
p{ text-align:justify; text-indent:1.3em; margin:0 0 .7em; }
h3.chapter + p::first-letter,
p.first::first-letter{ font-size:2.9em; line-height:.82; float:left; padding-right:.07em; color:#9a7b3f; }
blockquote{ margin:1.3em 1.8em; text-align:center; font-style:italic; }
blockquote p{ text-indent:0; }
blockquote cite{ display:block; font-size:8.5pt; font-style:normal; letter-spacing:.09em;
  text-transform:uppercase; margin-top:.4em; color:#555; }
.orn{ text-align:center; letter-spacing:1em; color:#9a7b3f; margin:1.7em 0; }
.about,.backcover{ page-break-before:always; }
.about h2,.backcover h2{ text-align:center; font-size:13pt; letter-spacing:.1em; text-transform:uppercase; font-weight:400; margin:0 0 1.4em; }
.about p,.backcover p{ text-align:center; text-indent:0; max-width:30em; margin:0 auto .85em; }
"""

def render_html(cfile, cover_rel):
    blocks=parse_blocks()
    parts=[]  # (kind,html)
    first=True
    for kind,text in blocks:
        if kind=='h1':
            parts.append(('h1',f'<h2 class="part">{esc(text)}</h2>'))
        elif kind=='h2':
            parts.append(('h2',f'<h3 class="chapter">{esc(text)}</h3>'))
        elif kind in ('p','em'):
            cls=' class="first"' if (kind=='p' and first) else ''
            if kind=='p': first=False
            if scripture(text):
                dash=text.rfind(' - ')
                q,attrib=text[1:dash],text[dash+3:-1]
                parts.append(('p',f'<blockquote><p>&ldquo;{esc(q)}&rdquo;</p><cite>{esc(attrib)}</cite></blockquote>'))
            else:
                parts.append(('p',f'<p{cls}>{inline(text)}</p>'))
        elif kind=='verse':
            parts.append(('p',f'<blockquote><p>{esc(text)}</p></blockquote>'))
        elif kind=='orn':
            parts.append(('p','<p class="orn">&#10022;&nbsp;&nbsp;&#10022;&nbsp;&nbsp;&#10022;</p>'))

    body='\n'.join(h for _,h in parts)

    html_doc=f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{esc(TITLE)}</title>
<style>{PRINT_CSS}</style></head><body>

<div class="cover-page">
  <img src="{cover_rel}{esc(cfile)}" alt="Cover">
</div>

<div class="title-page">
  <h1>Renaissance<br>of the Poor Soul</h1>
  <p class="sub">{esc(SUBTITLE)}</p>
  <p class="by">{esc(AUTHOR)}</p>
</div>

<div class="copyright-page page-break">
  <p style="letter-spacing:.05em">{esc(TITLE)}</p>
  <p style="font-style:italic; margin-bottom:2em">{esc(SUBTITLE)}<br>{esc(AUTHOR)}</p>
  <p>Copyright &#169; 2026 {esc(AUTHOR)}</p>
  <p style="margin-bottom:1.6em">All rights reserved.</p>
  <p class="lstext">No part of this book may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other non-commercial uses permitted by copyright law.</p>
  <p style="margin:1.2em 0 .3em"><strong>ISBN (Print): {ISBN_PRINT}</strong></p>
  <p>First published 2026</p>
  <p>Published in South Africa</p>
  <p style="font-size:8pt; margin-top:1.6em; color:#555">Scripture quotations are from the Holy Bible and are used for spiritual reference and commentary.</p>
</div>

<div class="contents page-break">
  <h2 style="text-align:center; font-size:13pt; letter-spacing:.1em; text-transform:uppercase; font-weight:400">Contents</h2>
  <p>Part One — Displacement</p>
  <p>Part Two — Confrontation</p>
  <p>Part Three — Cracking Open</p>
  <p>Part Four — Reframing</p>
  <p>Part Five — Rest and Becoming</p>
  <p>About the Author</p>
</div>

{body}

</body></html>'''
    return html_doc

def build(cid, cfile):
    d=os.path.join(PRINT,cid,'book'); os.makedirs(d,exist_ok=True)
    # cover image relative to print/coverX/book/ -> ../../book_design/
    cover_rel='../../../book_design/'
    html_path=os.path.join(d,'interior.html')
    with open(html_path,'w') as f:
        f.write(render_html(cfile, cover_rel))
    pdf_path=os.path.join(d,'interior.pdf')
    cmd=[CHROME,'--headless','--no-sandbox','--disable-gpu','--no-pdf-header-footer',
         f'--print-to-pdf={pdf_path}','file://'+html_path]
    r=subprocess.run(cmd,capture_output=True)
    if r.returncode!=0:
        raise RuntimeError(r.stderr.decode()[:500])
    return html_path, pdf_path

def main():
    os.makedirs(PRINT,exist_ok=True)
    for i,cfile in enumerate(COVERS):
        cid=f'cover{i+1}'
        h,p=build(cid,cfile)
        print(f"{cid}: interior.pdf {os.path.getsize(p)} B")

if __name__=='__main__':
    main()
