"""Feasibility check: PyMuPDF extraction + page-tagged chunking + BM25 retrieval.
Usage: python feasibility_bm25.py <folder with the 4 PDFs>"""
import sys, re, time, json, pathlib
import pymupdf
from rank_bm25 import BM25Okapi

DOCS = {"ErrorCodes.pdf": "UR Error Codes Directory",
        "710-965-00_UR5e_User_Manual_en_Global.pdf": "UR5e User Manual",
        "2F-85_2F-140_UR_PDF_20200211.pdf": "Robotiq 2F-85/2F-140 Manual",
        "e-Series_Service_Manual_en.pdf": "UR e-Series Service Handbook"}
CHUNK, OVERLAP = 800, 100

def tokenize(t):  # keep codes like C157A2 intact, keep stop words
    return re.findall(r"[a-z0-9]+", t.lower())

folder = pathlib.Path(sys.argv[1])
chunks, t0, pages = [], time.time(), 0
for fn, name in DOCS.items():
    doc = pymupdf.open(folder / fn)
    for pno, page in enumerate(doc, start=1):
        text = " ".join(page.get_text().split())
        pages += 1
        for s in range(0, max(len(text), 1), CHUNK - OVERLAP):
            piece = text[s:s + CHUNK]
            if len(piece) > 50:
                chunks.append({"doc": name, "page": pno, "text": piece})
t_ext = time.time() - t0
bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])
print(f"pages={pages} chunks={len(chunks)} extraction_s={t_ext:.1f}")

queries = ["C157A2",
           "What does C153 position deviates from path mean",
           "The robot keeps dropping parts",
           "How do I set the payload for a new gripper",
           "gripper lost the object"]
out = []
for q in queries:
    t = time.time(); sc = bm25.get_scores(tokenize(q)); dt = (time.time() - t) * 1000
    top = sorted(range(len(sc)), key=lambda i: -sc[i])[:5]
    hits = [(chunks[i]["doc"], chunks[i]["page"]) for i in top]
    out.append({"query": q, "ms": round(dt, 1), "top5": hits})
    print(f"\nQ: {q}  ({dt:.0f} ms)")
    for d, p in hits: print(f"   {d}, p. {p}")
json.dump(out, open("feasibility_results.json", "w"), indent=1)
