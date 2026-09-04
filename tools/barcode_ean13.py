#!/usr/bin/env python3
"""Generate a standards-compliant EAN-13 barcode PNG (offline, Pillow-only).

Encoding per GS1 EAN-13:
  - 95 modules: 103 left (guard+L/G-left6+guard) + 7 center guard + 42 right (right6+guard).
  - Left 6 digits: L or G coding selected by first digit's parity table.
  - Right 6 digits: R coding (complement of L).
  - ISBN/EAN book prefix 978 uses all-L left coding for the 6 chars after 978.
Draws at high scale, then downscales with LANCZOS to the requested pixel size for
a crisp, clean barcode. Includes guard bars extended taller and the human-readable
digits printed beneath.

Usage:  barcode_ean13.py <13-digit> <outfile> <width_px> <height_px> [dpi]
"""
import sys
from PIL import Image, ImageDraw, ImageFont

# digit -> L / G / R code (each '1'=bar)
L = ['0001101','0011001','0010011','0111101','0100011','0110001','0101111',
     '0111011','0110111','0001011']
G = ['0100111','0110011','0011011','0100001','0011101','0111001','0000101',
     '0010001','0001001','0010111']
R = ['1110010','1100110','1101100','1000010','1011100','1001110','1010000',
     '1000100','1001000','1110100']

# parity patterns for left half, selected by first digit
PARITY = {
  '0':'LLLLLL','1':'LLGLGG','2':'LLGGLG','3':'LLGGGL','4':'LGLLGG',
  '5':'LGGLLG','6':'LGGGLL','7':'LGLGLG','8':'LGLGGL','9':'LGGLGL'}

def ean13_bits(code):
    digits=[int(c) for c in code]
    if len(digits)!=13:
        raise ValueError('EAN-13 requires 13 digits')
    # validate check digit
    s=sum(d*(1 if i%2==0 else 3) for i,d in enumerate(digits[:12]))
    check=(10-(s%10))%10
    if check!=digits[12]:
        raise ValueError(f'bad check digit: got {digits[12]} expected {check}')
    first=digits[0]; left=digits[1:7]; right=digits[7:13]
    pat=PARITY[str(first)]
    sb=['101']                       # left guard
    for d,p in zip(left,pat):
        sb.append(L[d] if p=='L' else G[d])
    sb.append('01010')               # center guard
    for d in right:
        sb.append(R[d])
    sb.append('101')                 # right guard
    bits=''.join(sb)
    return bits, digits

def render(code, out, width_px=1500, height_px=900, dpi=300):
    bits, digits = ean13_bits(code)
    n=len(bits)                       # 95 modules
    # supersample for crisp rendering
    SCALE=8
    SS_W=width_px*SCALE; SS_H=int(height_px*SCALE*1.0)
    SS_H=max(SS_H, int(SS_W*0.5))
    img=Image.new('L',(SS_W,SS_H),255)
    dr=ImageDraw.Draw(img)
    module=SS_W/n
    x=0.0
    guard_h=SS_H
    text_h=int(SS_H*0.16)
    bar_h=SS_H-text_h
    # guard bar positions: left guard i0-2, center guard i45-49, right guard i92-94
    for i,b in enumerate(bits):
        x0=int(x); x1=max(x0+1,int(x+module))
        if b=='1':
            is_guard=(i<3 or 45<=i<=49 or i>=92)
            top=0
            # guards descend farther (into digit zone) for the classic longer bars
            bottom = SS_H-int(text_h*0.25) if is_guard else bar_h
            dr.rectangle([x0,top,x1,bottom], fill=0)
        x+=module
    # human-readable digits
    try:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
                                int(SS_H*0.085))
    except Exception:
        font=ImageFont.load_default()
    text=str(digits[0])+' '+''.join(map(str,digits[1:7]))+' '+''.join(map(str,digits[7:13]))
    tw=dr.textlength(text,font=font)
    dr.text(((SS_W-tw)/2, SS_H-text_h+int(SS_H*0.02)), text, fill=0, font=font)
    img=img.resize((width_px,height_px),Image.LANCZOS)
    img.save(out, dpi=(dpi,dpi))
    return out

if __name__=='__main__':
    code=sys.argv[1]
    out=sys.argv[2]
    w=int(sys.argv[3]) if len(sys.argv)>3 else 1500
    h=int(sys.argv[4]) if len(sys.argv)>4 else 900
    d=int(sys.argv[5]) if len(sys.argv)>5 else 300
    render(code,out,w,h,d)
    print('wrote',out,w,h)
