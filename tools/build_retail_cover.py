#!/usr/bin/env python3
"""Physical-retail wraparound cover generator for all 5 cover designs.

For each cover builds (300 DPI):
  - BACK panel: blurb + barcode + legal text, matched to front palette.
  - SPINE     : width = interior_pages * 0.0025in, colored to match.
  - FRONT panel: full-bleed source cover art.
Then flattens BACK+SPINE+FRONT into a single print-ready PDF and PNG:
  Renaissance_of_the_Poor_Soul/book_formats/print/coverX/cover/cover_final.pdf
also cover_final.png.

Back-cover layout (bottom right): EAN-13 barcode ~1.5in x 1in,
legal text (ISBN / Printed in South Africa / copyright) beneath.
No price is printed on the cover.
"""
import os, subprocess, re, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageDraw, ImageFont
import barcode_ean13

ROOT='/home/win/liviyo_pc/job/websites/liviyo_capital/working_sites/jobs_renaissance/Renaissance_of_the_Poor_Soul'
COVER_DIR=os.path.join(ROOT,'book_design')
OUT_ROOT=os.path.join(ROOT,'book_formats','print')
FONT_DIR='/usr/share/fonts/truetype/dejavu'

ISBN='978-1-0492-8328-9'
ISBN_RAW='9781049283289'
TITLE='Renaissance of the Poor Soul'
SUBTITLE='A journey through the many faces of the human spirit'
AUTHOR='Halalisani Ngema'
DPI=300
# A5 trim (148 x 210 mm) @300dpi => 1748 x 2480 px
PANEL_W, PANEL_H = 1748, 2480
SPINE_IN_PER_PAGE=0.0025
COVERS=['cover1.png','cover2.png','cover3.png','cover4.png','cover5.png']

GOLD=(201,168,92)
CREAM=(245,240,230)
SOFT=(213,203,182)

def serif(sz):
    return ImageFont.truetype(os.path.join(FONT_DIR,'DejaVuSerif.ttf'),sz)
def serifb(sz):
    return ImageFont.truetype(os.path.join(FONT_DIR,'DejaVuSerif-Bold.ttf'),sz)

def interior_pages(cid):
    p=os.path.join(ROOT,'print',cid,'book','interior.pdf')
    if os.path.exists(p):
        out=subprocess.run(['pdfinfo',p],capture_output=True,text=True).stdout
        m=re.search(r'Pages:\s+(\d+)',out)
        if m: return int(m.group(1))
    return 62

def back_bg(cfile):
    """Exact matched background tone + accent gold from each front."""
    im=Image.open(os.path.join(COVER_DIR,cfile)).convert('RGB')
    w,h=im.size
    # average of edge margins for a clean continuous background
    margin=int(w*0.06)
    strips=[
        im.crop((0,0,w,margin)),            # top
        im.crop((0,h-margin,w,h)),          # bottom
        im.crop((0,0,margin,h)),            # left
        im.crop((w-margin,0,w,h)),          # right
    ]
    tot=[0,0,0]; n=0
    for s in strips:
        px=list(s.resize((20,20),Image.LANCZOS).getdata())
        for p in px: 
            for k in range(3): tot[k]+=p[k]
            n+=1
    bg=tuple(tot[k]//n for k in range(3))
    return bg

def barcode_image():
    """Render EAN-13 at print size (1.5in x 1.0in @300dpi => 450x300) with digits."""
    W,H=450,300
    tmp=os.path.join(tempfile.mkdtemp(),'bc.png')
    barcode_ean13.render(ISBN_RAW, tmp, 1500, 900, 300)
    im=Image.open(tmp).convert('L')
    # crop tight to bars + digits, then place at target size
    # find content bbox
    px=im.load(); w,h=im.size
    xs=[x for x in range(w) if any(px[x,y]<128 for y in range(80,820))]
    ys=[y for y in range(h) if any(px[x,y]<128 for x in range(0,w,3))]
    x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
    crop=im.crop((x0,y0,x1+1,y1+1))
    target_w,target_h=W-40,H  # leave margin; keep aspect -> scale to width
    scale=target_w/crop.width
    nh=int(crop.height*scale)
    if nh>H:
        scale=H/crop.height; nh=H; target_w=int(crop.width*scale)
    resized=crop.resize((target_w,nh),Image.LANCZOS)
    canvas=Image.new('L',(W,H),255)
    canvas.paste(resized,((W-target_w)//2,(H-nh)//2))
    return canvas

def wrap_text(text,font,maxw):
    lines=[]
    for para in text.split('\n'):
        words=para.split(); cur=''
        for w in words:
            t=(cur+' '+w).strip()
            if font.getlength(t)<=maxw: cur=t
            else:
                if cur: lines.append(cur)
                cur=w
        if cur: lines.append(cur)
    return lines

def make_back(bg, cfile):
    W,H=PANEL_W,PANEL_H
    img=Image.new('RGB',(W,H),bg)
    dr=ImageDraw.Draw(img)
    # subtle darker vignette band at very top for elegance? keep simple + matched.
    # ---- top band: author/title markers ----
    dr.text((70,70), 'R E N A I S S A N C E   O F   T H E   P O O R   S O U L',
            font=serif(30), fill=SOFT)
    dr.text((70,120), AUTHOR.upper(), font=serif(28), fill=GOLD)
    # subtle horizontal rule under header
    dr.line([(70,175),(W-70,175)], fill=tuple(int(c*0.9) for c in bg), width=2)

    # ---- blurb (centered block) ----
    blurb=("Nothing is wrong with you.\nYou have prayed, tried, and done everything you "
           "were told, and still found yourself in the wrong place, overlooked, passed by, "
           "standing at doors that would not open. It is not.\n\nRenaissance of the Poor Soul "
           "is for every soul that has been afflicted, lost, restless, tormented, weary, and "
           "still refused to stop believing. It offers the company of honesty, the comfort of "
           "being truly understood, and the quiet, stubborn promise that the darkness will not "
           "have the last word.\n\nYour renaissance is not behind you. It is ahead.")
    fs=44
    lines=wrap_text(blurb, serif(fs), int(W*0.80))
    y=320
    for ln in lines:
        dr.text((W//2, y), ln, font=serif(fs), fill=CREAM, anchor='ma'); y+=int(fs*1.62)
        if ln.strip()=='' : y+=int(fs*0.6)

    # ---- bottom-right region: barcode ----
    bc_w, bc_h = 450, 300         # 1.5in x 1.0in @300dpi
    pad=70
    bx0 = W - bc_w - pad          # right margin
    bc=barcode_image()
    # white panel behind barcode for quiet zone/legibility (book retail standard)
    panel=Image.new('RGB',(bc_w+30,bc_h+30),(250,250,247))
    panel.paste(bc, (15,15))
    img.paste(panel,(bx0-15, H - bc_h - pad*2 - 15))

    # ---- legal text block (bottom-left, and under barcode) ----
    legal_y = H - pad*2 - 60
    lf=serif(30)
    legal=['ISBN %s'%ISBN, 'Published in South Africa', 'Printed in South Africa',
           'Copyright \u00a9 2026 Halalisani Ngema', 'All rights reserved']
    ll_y = H - pad*2 - 10
    for txt in legal:
        dr.text((70, ll_y), txt, font=lf, fill=SOFT, anchor='lm'); ll_y-=46
    return img

def make_front(cfile):
    front=Image.open(os.path.join(COVER_DIR,cfile)).convert('RGB')
    scale=max(PANEL_W/front.width, PANEL_H/front.height)
    nw,nh=round(front.width*scale),round(front.height*scale)
    front=front.resize((nw,nh),Image.LANCZOS)
    left=(nw-PANEL_W)//2
    return front.crop((left,0,left+PANEL_W,PANEL_H))

def build(cid,cfile):
    pages=interior_pages(cid)
    spine=max(1,round(pages*SPINE_IN_PER_PAGE*DPI))
    W=PANEL_W+spine+PANEL_W; H=PANEL_H
    bg=back_bg(cfile)
    back=make_back(bg,cfile)
    front=make_front(cfile)
    canvas=Image.new('RGB',(W,H),bg)
    canvas.paste(back,(0,0))
    # spine: slightly darkened matched tone with thin rules
    sp=Image.new('RGB',(spine,H),tuple(int(c*0.93) for c in bg))
    canvas.paste(sp,(PANEL_W,0))
    # thin gold rules on spine edges for a premium bound look
    sd=ImageDraw.Draw(canvas)
    sd.line([(PANEL_W,0),(PANEL_W,H)],fill=GOLD,width=2)
    sd.line([(PANEL_W+spine,0),(PANEL_W+spine,H)],fill=GOLD,width=2)
    canvas.paste(front,(PANEL_W+spine,0))

    d=os.path.join(OUT_ROOT,cid,'cover'); os.makedirs(d,exist_ok=True)
    png=os.path.join(d,'cover_final.png')
    pdf=os.path.join(d,'cover_final.pdf')
    canvas.save(png,dpi=(DPI,DPI))
    canvas.save(pdf,resolution=DPI)
    # companion: flat interior still lives separately; also drop cover_preview.html copy
    return pdf,png,pages,spine/DPI

def main():
    for i,c in enumerate(COVERS):
        cid=f'cover{i+1}'
        pdf,png,pages,sin=build(cid,c)
        print(f"{cid}: {sin:.3f}in spine ({round(sin*DPI)}px) pages={pages} -> {os.path.basename(pdf)}")

if __name__=='__main__':
    main()
