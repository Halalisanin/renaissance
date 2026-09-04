#!/usr/bin/env python3
"""Print-ready wraparound COVER generation for each cover design.

Layout (300 DPI), left to right: BACK panel + SPINE + FRONT panel.
  - Front : source cover (1587x2245) upscaled to full-bleed 6x9in (1800x2700px).
  - Spine : width = interior_pages * 0.0025 in, solid color sampled from cover.
  - Back  : solid sampled background + blurb + title/author + PRINT ISBN + barcode box.
Output: print/coverX/cover/cover.pdf  (single full-bleed PDF, no trim marks)
"""
import os, re, subprocess

ROOT = '/home/win/liviyo_pc/job/websites/liviyo_capital/working_sites/jobs_renaissance/Renaissance_of_the_Poor_Soul'
COVER_DIR = os.path.join(ROOT, 'book_design')
PRINT = os.path.join(ROOT, 'print')
CHROME = '/home/win/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'

ISBN_PRINT = '978-1-0492-8328-9'
TITLE = 'Renaissance of the Poor Soul'
SUBTITLE = 'A journey through the many faces of the human spirit'
AUTHOR = 'Halalisani Ngema'
COVERS = ['cover1.png','cover2.png','cover3.png','cover4.png','cover5.png']
DPI = 300
PANEL_W, PANEL_H = 6*DPI, 9*DPI          # 1800 x 2700
SPINE_IN_PER_PAGE = 0.0025
BLURB = ("Nothing is wrong with you. You have prayed, tried, and done everything you "
         "were told, and still found yourself standing at doors that would not open. "
         "It is not the problem you think it is.\n"
         "Renaissance of the Poor Soul is for every soul that has been afflicted, lost, "
         "restless, tormented, weary, and still refused to stop believing. It offers the "
         "company of honesty, the comfort of being truly understood, and the quiet, "
         "stubborn promise that the darkness will not have the last word.\n"
         "Your renaissance is not behind you. It is ahead.")

def interior_pages(cid):
    p=os.path.join(PRINT,cid,'book','interior.pdf')
    out=subprocess.run(['pdfinfo',p],capture_output=True,text=True).stdout
    m=re.search(r'Pages:\s+(\d+)',out)
    return int(m.group(1)) if m else 62

def build(cid, cfile):
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    pages=interior_pages(cid)
    spine = max(1, round(pages*SPINE_IN_PER_PAGE*DPI))
    W = PANEL_W + spine + PANEL_W
    H = PANEL_H

    front = Image.open(os.path.join(COVER_DIR,cfile)).convert('RGB')
    # cover-fit front into PANEL_W x PANEL_H (crop horizontal overflow)
    scale = max(PANEL_W/front.width, PANEL_H/front.height)
    nw,nh = round(front.width*scale), round(front.height*scale)
    front = front.resize((nw,nh), Image.LANCZOS)
    left = (nw-PANEL_W)//2
    front = front.crop((left,0,left+PANEL_W,PANEL_H))

    # sample background from left edge strip (mid) of original art for spine/back
    orig = Image.open(os.path.join(COVER_DIR,cfile)).convert('RGB')
    sw,sh = orig.size
    strip = orig.crop((0, int(sh*0.35), int(sw*0.04), int(sh*0.65)))
    px = list(strip.resize((1,1), Image.LANCZOS).getdata())[0]
    bg = tuple(px)

    canvas = Image.new('RGB',(W,H), bg)
    # back panel (left)
    canvas.paste(Image.new('RGB',(PANEL_W,PANEL_H), bg), (0,0))
    # spine
    sp = Image.new('RGB',(spine,H), tuple(int(c*0.92) for c in bg))
    canvas.paste(sp,(PANEL_W,0))
    # front panel (right)
    canvas.paste(front, (PANEL_W+spine,0))

    draw = ImageDraw.Draw(canvas)
    # ---- BACK typography ----
    bw0 = PANEL_W
    gold=(201,168,92)
    def font(sz):
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', sz)
    def fontb(sz):
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', sz)
    cx = bw0//2
    # blurb
    fs=40
    f=font(fs)
    wrap=wrap_text(BLURB, f, int(bw0*0.74))
    y=270
    for line in wrap:
        draw.text((cx, y), line, font=f, fill=(245,240,230), anchor='ma'); y+=int(fs*1.55)
    # divider
    draw.line([(cx-int(bw0*0.2), y+10),(cx+int(bw0*0.2), y+10)], fill=(190,175,150), width=2)
    y+=70
    # title / subtitle / author
    ft=fontb(58)
    draw.text((cx,y), TITLE, font=ft, fill=(250,246,240), anchor='ma'); y+=80
    fs2=34
    draw.text((cx,y), SUBTITLE, font=font(34), fill=(215,205,185), anchor='ma'); y+=70
    draw.text((cx,y), AUTHOR.upper(), font=font(28), fill=gold, anchor='ma'); y+=120
    # barcode box + ISBN (white quiet-zone required for scannability)
    bbw,bbh=int(bw0*0.42), int(bw0*0.20)
    bx0,by0=cx-bbw//2, y
    # white quiet zone behind barcode
    qz=14
    draw.rectangle([bx0-qz,by0-qz,bx0+bbw+qz,by0+bbh+qz+46], fill=(250,250,248))
    nbars=20
    for i in range(nbars):
        if i%2==0:
            x1=bx0+i*(bbw//nbars)
            draw.rectangle([x1, by0, x1+bbw//nbars, by0+bbh], fill=(15,15,15))
    draw.rectangle([bx0,by0+bbh,bx0+bbw,by0+bbh+6], fill=(15,15,15))
    draw.text((cx, by0+bbh+40), ISBN_PRINT, font=font(30), fill=(25,25,25), anchor='ma')
    y=by0+bbh+120
    draw.text((cx, int(H-90)), 'Liviyo', font=font(30), fill=(215,205,185), anchor='ma')
    draw.text((bx0, 60), 'RENAISSANCE OF THE POOR SOUL', font=font(26), fill=(215,205,185), anchor='la')
    draw.text((bx0, 110), AUTHOR, font=font(26), fill=(215,205,185), anchor='la')

    # ---- SPINE ----
    # solid; optionally a thin rule off the front. Keep clean for thin spine.

    canvas = canvas.convert('RGB')
    d=os.path.join(PRINT,cid,'cover'); os.makedirs(d,exist_ok=True)
    png_path=os.path.join(d,'cover.png')
    canvas.save(png_path, dpi=(DPI,DPI))
    # single-page PDF at exact physical 300 DPI size (points = px/300*72)
    pdf_path=os.path.join(d,'cover.pdf')
    canvas.save(pdf_path, resolution=DPI)
    return pdf_path, pages, spine/DPI

def wrap_text(text, font, maxw):
    lines=[]
    for para in text.split('\n'):
        words=para.split()
        cur=''
        for w in words:
            t=(cur+' '+w).strip()
            if font.getlength(t)<=maxw:
                cur=t
            else:
                if cur: lines.append(cur)
                cur=w
        if cur: lines.append(cur)
    return lines

def main():
    for i,cfile in enumerate(COVERS):
        cid=f'cover{i+1}'
        p,pages,sin=build(cid,cfile)
        print(f"{cid}: cover.pdf OK pages={pages} spine={sin:.3f}in = {round(sin*DPI)}px @300dpi -> {os.path.getsize(p)} B")

if __name__=='__main__':
    main()
