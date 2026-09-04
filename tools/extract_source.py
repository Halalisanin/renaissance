#!/usr/bin/env python3
"""Canonical source extractor for 'Renaissance of the Poor Soul'.

Reads the FINAL (3) DOCX and writes a clean, annotated Markdown master
(stored at Renaissance_of_the_Poor_Soul/source/book.md). All formats are
generated from this Markdown master.

A proper copyright page carrying BOTH ISBNs (print + electronic) is inserted
after the title page (the source DOCX copyright block only lists the eISBN).
"""
import os, re
from docx import Document

ROOT = '/home/win/liviyo_pc/job/websites/liviyo_capital/working_sites/jobs_renaissance/Renaissance_of_the_Poor_Soul'
SRC = os.path.join(ROOT, 'Renaissance of the Poor Soul - Halalisani Ngema - FINAL (3).docx')
OUT = os.path.join(ROOT, 'source', 'book.md')

ISBN_PRINT = '978-1-0492-8328-9'
ISBN_ELEC  = '978-1-0492-8329-6'

PART_HEAD = {'PART ONE','PART TWO','PART THREE','PART FOUR','PART FIVE'}
PART_TITLE = {'DISPLACEMENT','CONFRONTATION','CRACKING OPEN','REFRAMING','REST AND BECOMING'}

def is_scripture(t):
    return t.startswith('"') and ' - ' in t and t.rstrip().endswith('"')

def copyright_page():
    return f"""# Copyright

**Renaissance of the Poor Soul**
*A journey through the many faces of the human spirit*
*Halalisani Ngema*

Copyright © 2026 Halalisani Ngema. All rights reserved.

No part of this book may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other non-commercial uses permitted by copyright law.

**ISBN (Print):** {ISBN_PRINT}
**ISBN (Electronic):** {ISBN_ELEC}

First published 2026
Published in South Africa

Scripture quotations are from the Holy Bible and are used for spiritual reference and commentary."""

def markdown_title(name):
    return f"\n# {name}\n"

def main():
    doc = Document(SRC)
    P = doc.paragraphs

    def txt(*idxs):
        out = []
        for i in idxs:
            t = P[i].text.strip()
            if t:
                out.append(t)
        return out

    # ---------- Front matter (explicit, clean) ----------
    fm = []
    fm.append("# Renaissance of the Poor Soul\n")
    fm.append("*A journey through the many faces of the human spirit*\n")
    fm.append("*Halalisani Ngema*\n")
    fm.append("\n---\n")
    fm.append(copyright_page())
    fm.append("\n---\n")

    # Dedication
    fm.append(markdown_title('Dedication'))
    fm.extend(f"{d}\n" for d in txt(34,35,36,37))
    fm.append("\n---\n")

    # For every soul epigraph
    fm.append("*For every soul that has wandered, wept, and waited.*\n")
    fm.append("*Your time is coming.*\n")
    fm.append("\n---\n")

    # Mkhize prayer
    fm.append("> "+"  \n> ".join(txt(46,47,48))+"\n")
    fm.append("\n---\n")

    # Foreword
    fm.append(markdown_title('Foreword'))
    fm.extend(f"{d}\n" for d in txt(52,54,56,57,58,59,61,62,63,65,66))
    fm.append("\n---\n")

    # Introduction
    fm.append(markdown_title('Introduction'))
    fm.extend(f"{d}\n" for d in txt(70,72,73,74,75,76,78,79,81,82,84))
    fm.append("\n---\n")

    # Contents (built from the DOCX TOC, paras 90-113)
    fm.append(markdown_title('Contents'))
    toc = """Part One — Displacement
01 What Is the Soul? · 02 The Poor Soul · 03 The Afflicted Soul

Part Two — Confrontation
04 The Poor and Afflicted Soul · 05 The Lost Soul · 06 The Restless Soul · 07 The Tormented Soul

Part Three — Cracking Open
08 The Weary Soul · 09 The Ancient Soul · 10 Modern Soul Archetypes

Part Four — Reframing
11 The Seeking Soul · 12 The Awakened Soul · 13 The Redeemed Soul · 14 No Soul Beyond Reach

Part Five — Rest and Becoming
15 Surviving the Long Night"""
    fm.append(toc)
    fm.append("\n---\n")

    # ---------- Body (paras 119..470, the main manuscript) ----------
    body = []
    started = False
    END = 470
    for i in range(119, END):
        t = P[i].text.strip()
        if not t:
            continue
        u = t.upper()
        if u == 'ABOUT THE AUTHOR' or u == 'BACK COVER':
            break
        if u in PART_HEAD:
            body.append(markdown_title(t))
            continue
        if u in PART_TITLE:
            body.append(f"\n## {t}\n")
            continue
        if t == '○ ○ ○':
            body.append("\n* * *\n")
            continue
        if t == '○' or t.isdigit():
            continue
        if u in ('THE END','END'):
            body.append(f"\n*{t}*\n")
            continue
        if t.isupper() and len(t) <= 60 and not t.endswith('.') and re.match(r'^[A-Z 0-9?]+$', t) and not u.startswith('PART'):
            body.append(f"\n## {t}\n")
            continue
        if is_scripture(t):
            body.append(f"\n> {t}\n")
            continue
        body.append(t)

    # ---------- About the Author (472-479) ----------
    about_title = "\n# About the Author\n"
    about_body = "\n".join(txt(474,475,476,477,478,479))
    # back-cover prayer (481-483)
    about_body += "\n\n> "+"  \n> ".join(txt(481,482,483))

    # ---------- Back Cover (487-504) ----------
    back_title = "\n# Back Cover\n"
    back_body = "\n".join(txt(490,492,494,496,498,500,502,503,504))

    out = '\n'.join(fm) + '\n' + '\n'.join(body) + '\n' + about_title + about_body + '\n' + back_title + back_body + '\n'

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        f.write(out)
    print("WROTE", OUT, "| chars:", len(out))

if __name__ == '__main__':
    main()
