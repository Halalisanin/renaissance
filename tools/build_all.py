#!/usr/bin/env python3
"""Production build for 'Renaissance of the Poor Soul'.

For each of the 5 covers generates:
  Digital : EPUB, DOCX, FB2, TXT, HTML, Markdown, reading-PDF  -> digital/<fmt>/coverX/
  Print   : interior.pdf + wraparound cover.pdf                 -> print/coverX/{book,cover}/

Electronic ISBN goes in digital metadata / reading-PDF copyright.
Print ISBN goes on the print interior copyright and cover back.
Source of truth: Renaissance_of_the_Poor_Soul/source/book.md
Requires: python-docx, Pillow, markdown; wkhtmltopdf, ghostscript, pdftotext.
"""
import os, re, html, base64, subprocess, sys

ROOT = '/home/win/liviyo_pc/job/websites/liviyo_capital/working_sites/jobs_renaissance/Renaissance_of_the_Poor_Soul'
MD_SRC = os.path.join(ROOT, 'source', 'book.md')
COVER_DIR = os.path.join(ROOT, 'book_design')
DIGITAL = os.path.join(ROOT, 'digital')
PRINT = os.path.join(ROOT, 'print')

ISBN_PRINT = '978-1-0492-8328-9'
ISBN_ELEC  = '978-1-0492-8329-6'
TITLE = 'Renaissance of the Poor Soul'
SUBTITLE = 'A journey through the many faces of the human spirit'
AUTHOR = 'Halalisani Ngema'

COVERS = ['cover1.png','cover2.png','cover3.png','cover4.png','cover5.png']
CHROME = '/home/win/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'

# ---------------------------------------------------------------------------
# Parse Markdown master
# ---------------------------------------------------------------------------
def parse_blocks():
    with open(MD_SRC) as f:
        raw = f.read()
    blocks = []
    in_break = False
    for ln in raw.split('\n'):
        l = ln.rstrip()
        s = l.strip()
        if not s or s == '---':
            continue
        if s.startswith('# ') and not s.startswith('## '):
            blocks.append(('h1', s[2:].strip()))
        elif s.startswith('## '):
            blocks.append(('h2', s[3:].strip()))
        elif s == '* * *':
            blocks.append(('orn', '* * *'))
        elif s.startswith('> '):
            blocks.append(('verse', s[2:].strip()))
        elif s.startswith('*') and s.endswith('*') and len(s) < 80 and s.count('*') <= 2:
            blocks.append(('em', s.strip('*')))
        else:
            blocks.append(('p', s))
    return blocks

def esc(x):
    return html.escape(x, quote=False)

def inline(s):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', esc(s))

# ---------------------------------------------------------------------------
# HTML digital body
# ---------------------------------------------------------------------------
CSS = """
@page{ size: 148mm 210mm; margin: 15mm 16mm 14mm 16mm; }
:root{ --bg:#faf6ee; --ink:#231e15; --gold:#9a7b3f; --muted:#6b6152; }
*{ box-sizing:border-box; }
body{ margin:0; background:var(--bg); color:var(--ink);
  font-family:Georgia,'Palatino Linotype','Times New Roman',serif; line-height:1.78; }
@media screen{ .page{ max-width:700px; margin:0 auto; padding:52px 26px 90px; } }
@media print{ .page{ max-width:none; padding:0; } }
header.hero{ text-align:center; padding:60px 0 10px; }
header.hero h1{ font-weight:400; font-size:2.55rem; letter-spacing:.015em; margin:0 0 .3em; }
header.hero .sub{ font-style:italic; font-size:1.16rem; color:var(--muted); margin:0 0 .5em; }
header.hero .by{ letter-spacing:.24em; text-transform:uppercase; font-size:.8rem; color:var(--gold); }
hr.rule{ border:0; border-top:1px solid #e0d7c0; width:54px; margin:2.4em auto; }
.cover{ text-align:center; margin:0 0 1.4em; }
.cover img{ width:min(250px,82%); box-shadow:0 26px 60px -24px rgba(0,0,0,.5); }
h2.part{ text-align:center; letter-spacing:.3em; text-transform:uppercase; font-weight:400;
  font-size:1.28rem; margin:3.2em 0 .5em; color:#8a6d33; }
h3.chapter{ text-align:center; font-weight:400; font-size:1.55rem; margin:2.6em 0 .5em; }
h3.chapter::after{ content:""; display:block; width:40px; height:1px; background:var(--gold); margin:1em auto 0; }
p{ text-align:justify; margin:0 0 1.1em; }
p.first::first-letter{ font-size:3em; line-height:.82; float:left; padding-right:.08em; color:var(--gold); }
blockquote{ margin:1.6em 2em; font-style:italic; color:#4f4636; border-left:2px solid var(--gold); padding-left:1.1em; }
.orn{ text-align:center; letter-spacing:1em; color:var(--gold); margin:2em 0; }
.cr{ text-align:center; color:var(--muted); font-size:.88rem; border-top:1px solid #e0d7c0; margin-top:3em; padding-top:1.6em; }
.cr strong{ color:var(--ink); display:block; margin-bottom:.3em; }
.cr p{ text-align:center; margin:0 0 .3em; }
footer{ text-align:center; color:var(--muted); font-size:.84rem; margin-top:2.6em; }
"""
def bodies_html(blocks, cr_block):
    out = []
    first = True
    for kind, text in blocks:
        if kind == 'h1':
            out.append(f'<h2 class="part">{esc(text)}</h2>')
        elif kind == 'h2':
            out.append(f'<h3 class="chapter">{esc(text)}</h3>')
        elif kind in ('p','em'):
            cls = ' class="first"' if (kind=='p' and first) else ''
            if kind=='p': first = False
            out.append(f'<p{cls}>{inline(text)}</p>')
        elif kind == 'verse':
            out.append(f'<blockquote><p>{esc(text)}</p></blockquote>')
        elif kind == 'orn':
            out.append('<p class="orn">&#10022;&nbsp;&nbsp;&#10022;&nbsp;&nbsp;&#10022;</p>')
    out.append(cr_block)
    return '\n'.join(out)

def digital_cr(cid):
    return f"""
<div class="cr">
<p><strong>{esc(TITLE)}</strong></p>
<p>Copyright &#169; 2026 {esc(AUTHOR)}. All rights reserved.</p>
<p>Electronic ISBN: <strong>{ISBN_ELEC}</strong></p>
<p>Print ISBN: <strong>{ISBN_PRINT}</strong></p>
</div>
<footer>Published 2026 &#183; South Africa</footer>"""

def html_doc(cover_src_attr, cid):
    blocks = parse_blocks()
    body = bodies_html(blocks, digital_cr(cid))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(SUBTITLE)}">
<title>{esc(TITLE)} — {esc(AUTHOR)}</title>
<style>{CSS}</style>
</head><body><div class="page">
<header class="hero">
<h1>{esc(TITLE)}</h1>
<p class="sub">{esc(SUBTITLE)}</p>
<p class="by">{esc(AUTHOR)}</p>
</header>
<div class="cover"><img id="coverImg" src="{cover_src_attr}" alt="Cover"></div>
{body}
</div></body></html>"""

# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
def build_markdown(cid):
    d = os.path.join(DIGITAL, 'markdown', cid); os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, f'renaissance_{cid}.md')
    with open(MD_SRC) as f: c = f.read()
    with open(dst,'w') as f: f.write(c)
    return dst

def build_txt(cid):
    blocks = parse_blocks()
    out=[]
    for kind,text in blocks:
        if kind=='h1':
            out += [text.upper(), '='*min(len(text),60), '', '']
        elif kind=='h2':
            out += [text.upper(), '']
        elif kind in ('p','em','verse'):
            out += [text,'']
        elif kind=='orn':
            out += ['* * *','']
    d=os.path.join(DIGITAL,'txt',cid); os.makedirs(d,exist_ok=True)
    dst=os.path.join(d,f'renaissance_{cid}.txt')
    with open(dst,'w') as f: f.write('\n'.join(out))
    return dst

def build_html(cid, cfile):
    d=os.path.join(DIGITAL,'html',cid); os.makedirs(d,exist_ok=True)
    dst=os.path.join(d,f'renaissance_{cid}.html')
    doc = html_doc(f'../../../../book_design/{cfile}', cid)
    with open(dst,'w') as f: f.write(doc)
    return dst

def build_epub(cid, cfile):
    import zipfile
    d=os.path.join(DIGITAL,'epub',cid); os.makedirs(d,exist_ok=True)
    dst=os.path.join(d,f'renaissance_{cid}.epub')
    body = bodies_html(parse_blocks(), digital_cr(cid))
    xhtml=f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en">
<head><meta charset="utf-8"/><title>{esc(TITLE)}</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body><div class="page">
<header class="hero"><h1>{esc(TITLE)}</h1><p class="sub">{esc(SUBTITLE)}</p><p class="by">{esc(AUTHOR)}</p></header>
<div class="cover"><img src="../Images/{cfile}" alt="Cover"/></div>
{body}
</div></body></html>'''
    opf=f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="en">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="uid">{ISBN_ELEC}</dc:identifier>
<dc:title>{esc(TITLE)}</dc:title>
<dc:creator>{esc(AUTHOR)}</dc:creator>
<dc:language>en</dc:language>
<dc:description>{esc(SUBTITLE)}</dc:description>
<dc:publisher>Liviyo</dc:publisher>
<dc:date>2026</dc:date>
<dc:rights>Copyright © 2026 Halalisani Ngema. All rights reserved.</dc:rights>
<dc:subject>Spirituality</dc:subject>
<meta property="dcterms:modified">2026-09-04T00:00:00Z</meta>
<meta name="cover" content="cover-img"/>
</metadata>
<manifest>
<item id="cover-img" href="Images/{cfile}" media-type="image/png" properties="cover-image"/>
<item id="css" href="style.css" media-type="text/css"/>
<item id="content" href="Text/content.xhtml" media-type="application/xhtml+xml"/>
<item id="nav" href="Text/nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
</manifest>
<spine><itemref idref="content"/></spine>
</package>'''
    container='''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>'''
    nav=f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Contents</title></head><body><nav epub:type="toc"><h1>Contents</h1><ol><li><a href="content.xhtml">{esc(TITLE)}</a></li></ol></nav></body></html>'''
    with open(os.path.join(COVER_DIR,cfile),'rb') as f: cover=f.read()
    with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml',container)
        z.writestr('OEBPS/content.opf',opf)
        z.writestr('OEBPS/style.css',CSS)
        z.writestr('OEBPS/Text/content.xhtml',xhtml)
        z.writestr('OEBPS/Text/nav.xhtml',nav)
        z.writestr(f'OEBPS/Images/{cfile}',cover)
    return dst

def build_fb2(cid, cfile):
    d=os.path.join(DIGITAL,'fb2',cid); os.makedirs(d,exist_ok=True)
    dst=os.path.join(d,f'renaissance_{cid}.fb2')
    body=[]
    sec_open=False
    def sec_close():
        nonlocal sec_open
        if sec_open:
            body.append('</section>'); sec_open=False
    for kind,text in parse_blocks():
        if kind=='h1':
            sec_close()
            body.append(f'<section><title><p>{esc_x(text)}</p></title>')
            sec_open=True
        elif kind=='h2':
            body.append(f'<subtitle>{esc_x(text)}</subtitle>')
        elif kind=='orn':
            body.append('<empty-line/>')
        elif kind=='verse':
            body.append(f'<poem><stanza><v>{esc_x(text)}</v></stanza></poem>')
        elif kind in ('p','em'):
            body.append(f'<p>{esc_x(text)}</p>')
    sec_close()
    with open(os.path.join(COVER_DIR,cfile),'rb') as f:
        cb=base64.b64encode(f.read()).decode()
    fb2=f'''<?xml version="1.0" encoding="utf-8"?>
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
<program-used>custom</program-used><id>{ISBN_ELEC}</id><version>1.0</version></document-info>
<publish-info><isbn>{ISBN_ELEC}</isbn></publish-info>
</description>
<body>{''.join(body)}\n</body>
<binary id="cover.png" content-type="image/png">{cb}</binary>
</FictionBook>'''
    with open(dst,'w') as f: f.write(fb2)
    return dst

def esc_x(s):
    return html.escape(s).replace('"','&quot;')

def build_docx(cid, cfile):
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    d=os.path.join(DIGITAL,'docx',cid); os.makedirs(d,exist_ok=True)
    dst=os.path.join(d,f'renaissance_{cid}.docx')
    doc=Document()
    st=doc.styles['Normal']; st.font.name='Georgia'; st.font.size=Pt(11); st.font.color.rgb=RGBColor(0x23,0x1e,0x15)
    def center(run,size,bold=False,italic=False):
        run.bold=bold; run.italic=italic; run.font.size=Pt(size)
    # title
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    center(p.add_run(TITLE),26)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    center(p.add_run(SUBTITLE),13,italic=True)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    center(p.add_run(AUTHOR),12)
    doc.add_page_break()
    # iterate blocks
    for kind,text in parse_blocks():
        if kind=='h1':
            p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            center(p.add_run(text),15,bold=True); doc.add_page_break()
        elif kind=='h2':
            p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            center(p.add_run(text),14); doc.add_page_break()
        elif kind=='orn':
            p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.add_run('* * *')
        elif kind=='verse':
            p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.add_run(text).italic=True
        elif kind in ('p','em'):
            t=re.sub(r'\*\*(.+?)\*\*',r'\1',text)
            doc.add_paragraph(t)
    # ISBN page at end
    doc.add_page_break()
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run('ISBN (Print): '+ISBN_PRINT)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run('ISBN (Electronic): '+ISBN_ELEC)
    doc.save(dst)
    return dst

# ---------------------------------------------------------------------------
# Reading PDF (digital) via wkhtmltopdf
# ---------------------------------------------------------------------------
def build_reading_pdf(cid, cfile):
    d=os.path.join(DIGITAL,'pdf',cid); os.makedirs(d,exist_ok=True)
    dst=os.path.join(d,f'renaissance_{cid}.pdf')
    html_tmp = os.path.join(tempfile_dir(), f'_reading_{cid}.html')
    with open(html_tmp,'w') as f:
        f.write(html_doc(f'../../../../book_design/{cfile}', cid))
    cmd=[CHROME,'--headless','--no-sandbox','--disable-gpu','--no-pdf-header-footer',
         f'--print-to-pdf={dst}', 'file://'+html_tmp]
    r=subprocess.run(cmd,capture_output=True)
    os.remove(html_tmp)
    if r.returncode!=0:
        raise RuntimeError('chrome pdf failed: '+r.stderr.decode()[:500])
    return dst

def tempfile_dir():
    import tempfile
    t=tempfile.mkdtemp(prefix='rps_')
    return t

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(DIGITAL,exist_ok=True); os.makedirs(PRINT,exist_ok=True)
    for i,cfile in enumerate(COVERS):
        cid=f'cover{i+1}'
        print(f"===== {cid} / {cfile} =====")
        for fn in (build_markdown, build_txt, build_html, build_epub, build_fb2, build_docx):
            try:
                p=fn(cid) if fn in (build_markdown, build_txt) else fn(cid,cfile)
                print(f"  {os.path.basename(p)}: OK ({os.path.getsize(p)} B)")
            except Exception as e:
                print(f"  ERROR {fn.__name__}: {e}")
        # reading pdf
        try:
            p=build_reading_pdf(cid,cfile); print(f"  reading-pdf: {p} ({os.path.getsize(p)} B)")
        except Exception as e:
            print(f"  ERROR reading-pdf: {e}")

if __name__=='__main__':
    main()
