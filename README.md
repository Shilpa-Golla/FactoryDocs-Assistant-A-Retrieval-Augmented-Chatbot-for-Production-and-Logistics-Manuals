# FactoryDocs Assistant

**A Retrieval-Augmented Chatbot for Robot Error Diagnosis in Production**

> Case Study: Intelligent Systems in Production (MDM-2) · Deggendorf Institute of Technology (THD)
> Track: Software & Simulation · Lecturer: Hamidreza Heidari, PhD

![Status](https://img.shields.io/badge/status-methodology%20%26%20design%20phase-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

---

## About the project

Collaborative robots like the Universal Robots UR5e are widely used in production, for example to load CNC machines or pick and place parts. In real operation, the robot often stops itself for safety (a protective stop) and shows an error code, such as C153 (position deviates from path) or C157 (collision detected by joint). When the robot stops, the connected machine and material flow stop too.

The cause and the fix are spread across several long manuals: the error code directory, the robot user manual, the gripper manual and the service handbook. Workers often describe the problem in their own words, which simple keyword search (Ctrl+F) cannot handle. General AI chatbots can give confident but wrong answers, which can damage machines or hurt people.


**FactoryDocs Assistant** lets the worker type the error code or the problem and answers **only** from these manuals, using Retrieval-Augmented Generation (RAG):

- Finds the relevant part of the manual
- A local language model writes a short answer
- **Every answer shows the source page**
- If the answer is not in the manuals, it says **"I don't know"** instead of guessing
- Runs **locally** with Ollama, so documents never leave the computer

## Input and output

**Input:** an error code (e.g., "C157A2") or a problem in the worker's own words (e.g., "The robot keeps dropping parts")

**Output:** meaning of the error, likely cause, fix steps, and source pages from the manuals, or "I don't know" if the answer is not in the manuals

## Real-world problem

- Protective stops are commonly caused by a wrong payload setting, collisions, dragging cables or high acceleration [8].
- Universal Robots requires that every protective stop is investigated before restarting: "Protective Stop warning message SHALL NOT be reset without a review to determine the fault's root cause" [8].
- Unplanned downtime costs the world's 500 largest companies about $1.4 trillion per year [7].

## How it works

```mermaid
flowchart LR
    A[PDF manuals] --> B[Extract text & tables]
    B --> C[Split into page-tagged chunks]
    C --> D[Index: FAISS embeddings + BM25 keywords]
    Q[Worker question] --> E[Retrieve top-k chunks]
    D --> E
    E --> F[Local LLM via Ollama]
    F --> G{Answer found in chunks?}
    G -- Yes --> H[Answer + source page]
    G -- No --> I["I don't know"]
```

## What we compare

All four approaches are tested on the same question set:

| # | Approach | Description |
|---|----------|-------------|
| 1 | Plain LLM | No retrieval, answers from the model's memory (shows hallucination risk) |
| 2 | BM25 RAG | Keyword search baseline |
| 3 | Dense RAG | Meaning-based search with sentence embeddings |
| 4 | Hybrid RAG | BM25 + dense search combined (handles exact error codes like C157A2 and problem descriptions) |

We also test different chunk sizes (400 / 800 / 1,000 characters) and top-k values (3 / 5 / 10). Hybrid search fuses the BM25 and dense rankings with Reciprocal Rank Fusion (RRF, k = 60).

## Current status: BM25 feasibility check

A first test on the real manuals (`src/feasibility_bm25.py`): PyMuPDF extraction, 800-character chunks with 100 overlap, BM25 keyword search, 5 example questions. This is a feasibility check, not the evaluation.

- 690 pages → 1,550 chunks, extracted in 1.8 s on a team laptop; each BM25 query takes under 10 ms
- The correct page was in the top 5 for **4 of 5** questions, e.g. "C157A2" → Error Codes Directory p. 35 (rank 1), "How do I set the payload for a new gripper" → UR5e User Manual p. 105 "Set Payload" (rank 1)
- **Missed:** "The robot keeps dropping parts" did not reach the gripper manual, because keyword search needs the manual's own words. This confirms the need for dense and hybrid retrieval.
- Table-of-contents pages appear in results (they list every code), so front matter will be filtered before indexing.

## Evaluation

**Test set:** 60 team-written questions in 5 types: error code, problem description, multi-document, procedure, and unanswerable.

| KPI | What it measures | Target |
|-----|------------------|--------|
| Retrieval hit rate@5 | Correct page is among the top 5 retrieved chunks | ≥ 80% |
| Answer accuracy | Answer judged correct (3-level rubric, 2 reviewers) | ≥ 75%, beats baselines |
| Refusal rate | Says "I don't know" on unanswerable questions | ≥ 80% |
| Response time | Median seconds per answer on a laptop | ≤ 10 s |

Targets are goals; final results will be added here after the experiments.

## Data

We use four public manuals for the UR5e robot and its gripper. **The PDFs are not stored in this repository** (copyright); download them from the original sources and place them in `data/raw/`.

| Document | What it gives | Source |
|---|---|---|
| UR Error Codes Directory | Meaning and suggested fix for robot error codes | [Universal Robots](https://www.universal-robots.com/manuals/EN/PDF/Shared/ErrorCodes/ErrorCodes.pdf) |
| UR5e User Manual | Robot settings, e.g., payload and safety | [Universal Robots](https://s3-eu-west-1.amazonaws.com/ur-support-site/262292/710-965-00_UR5e_User_Manual_en_Global.pdf) |
| Robotiq 2F-85 / 2F-140 Manual (for UR) | Gripper problems, e.g., dropped parts | [Robotiq](https://assets.robotiq.com/website-assets/support_documents/document/2F-85_2F-140_UR_PDF_20200211.pdf) |
| UR e-Series Service Handbook | Repair and troubleshooting steps | [Universal Robots](https://www.universal-robots.com/download/manuals-e-seriesur-series/service/service-manual-e-series-english/) |

## Tech stack

| Purpose | Tool |
|---------|------|
| PDF extraction | PyMuPDF (compared with pdfplumber) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector search | FAISS |
| Keyword search | rank-bm25 |
| Hybrid fusion | Reciprocal Rank Fusion (k = 60) |
| Language model | Ollama with Llama 3.1 8B, runs locally |
| Evaluation | pandas, RAGAS |
| Demo app | Streamlit |

## Repository structure (planned)

```
├── data/
│   ├── raw/              # downloaded PDFs (not committed)
│   ├── processed/        # extracted, chunked text
│   └── test_set.csv      # 60 evaluation questions with answers
├── src/
│   ├── feasibility_bm25.py  # first BM25 test on the manuals (done)
│   ├── extract.py        # PDF text and table extraction
│   ├── chunk.py          # page-tagged chunking
│   ├── index.py          # FAISS and BM25 indexes
│   ├── retrieve.py       # BM25, dense and hybrid retrieval
│   ├── generate.py       # LLM answering with citations / refusal
│   └── evaluate.py       # KPI calculation
├── app/
│   └── app.py            # Streamlit chat demo
├── results/              # metrics, tables, error analysis
├── docs/                 # proposal, slides, report
├── requirements.txt
└── README.md
```

## Getting started

### Run the feasibility check (works now)

```bash
# 1. Clone the repository
git clone https://github.com/Shilpa-Golla/FactoryDocs-Assistant-A-Retrieval-Augmented-Chatbot-for-Production-and-Logistics-Manuals.git
cd FactoryDocs-Assistant-A-Retrieval-Augmented-Chatbot-for-Production-and-Logistics-Manuals

# 2. Install Python packages
pip install -r requirements.txt

# 3. Download the 4 manuals (links under "Data") into data/raw/, then run
python src/feasibility_bm25.py data/raw
```

The script expects these file names in the folder: `ErrorCodes.pdf`, `710-965-00_UR5e_User_Manual_en_Global.pdf`, `2F-85_2F-140_UR_PDF_20200211.pdf`, `e-Series_Service_Manual_en.pdf`. It prints the top 5 pages per question and saves `feasibility_results.json`.

### Full system (planned)

These commands will work once the remaining code is added.

```bash
# Install Ollama (https://ollama.com) and download the model
ollama pull llama3.1:8b

# Build the indexes, then start the chat app
python src/index.py
streamlit run app/app.py
```

## Milestones

| Phase | Date | Deliverable | Status |
|-------|------|-------------|--------|
| P1 | 20 Oct 2026 | Proposal, tech stack, MVP definition | ✅ (revised after lecturer feedback) |
| P2 | 03 Nov 2026 | Bibliography report, input documents selected, test plan | ✅ |
| P3 | 24 Nov 2026 | Theoretical framework, methodology, system design; BM25 feasibility check | 🔄 |
| P4 | 08 Dec 2026 | Dense + hybrid retrieval, LLM answers with citations, full test set, first comparison | ⏳ |
| P5 | 22 Dec 2026 | Experiments, error analysis, Streamlit demo, demo video, run instructions | ⏳ |
| Final | 12 Jan 2027 | IEEE report and final presentation | ⏳ |

## Team

| Name | Role |
|------|------|
| Divi Teja Dimmiti | Team Lead · RAG pipeline and LLM integration |
| Shilpa Golla | PDF extraction and LLM integration |
| Vijay Boyapati | Evaluation and Streamlit demo |

The test set (60 questions) is written and checked by all three members.

## Safety notice

FactoryDocs Assistant is a **decision aid** for a university project. It is not a replacement for official manuals or safety procedures. Always check the cited page and follow your company's safety rules.

## References

1. P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," *NeurIPS*, 2020.
2. Y. Gao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey," arXiv:2312.10997, 2023.
3. S. Es et al., "RAGAS: Automated Evaluation of Retrieval Augmented Generation," *EACL (Demos)*, 2024.
4. N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," *EMNLP*, 2019.
5. J. Johnson, M. Douze and H. Jégou, "Billion-scale similarity search with GPUs," *IEEE Trans. Big Data*, vol. 7, no. 3, pp. 535–547, 2021.
6. S. Robertson and H. Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond," *Found. Trends Inf. Retr.*, 2009.
7. Siemens AG, "The True Cost of Downtime 2024," Siemens Digital Industries, 2024. [Online]. Available: https://assets.new.siemens.com/siemens/assets/api/uuid:1b43afb5-2d07-47f7-9eb7-893fe7d0bc59/TCOD-2024_original.pdf
8. Universal Robots, "Understanding Protective Stops," support article, 2026. [Online]. Available: https://www.universal-robots.com/articles/ur/robot-care-maintenance/understanding-protective-stops/
