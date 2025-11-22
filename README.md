# PYQ Extractor 🎯
### AKTU Previous Year Question Paper Downloader

**Built by:** Manish Dhangar | CSE-AI 

---

## What It Does

PYQ Extractor is a CLI tool that:
1. Takes a subject name as input (exact or approximate)
2. Fuzzy-matches it against a built-in AKTU subject database
3. Shows you matching subjects with subject codes and year info
4. After your confirmation, scrapes the source for all available PYQ PDFs
5. Downloads them to `~/Downloads/PYQ_Extractor/<SubjectName>/`

---

## Setup

### Requirements
- Python 3.8+
- Internet connection
- Parrot OS / any Linux distro (or Windows)

### Install dependencies

```bash
cd pyq_extractor
pip install -r requirements.txt
```

> On Parrot OS / Debian-based:
> ```bash
> pip install -r requirements.txt --break-system-packages
> ```

---

## Run

```bash
python3 pyq_extractor.py
```

Or make it executable:
```bash
chmod +x pyq_extractor.py
./pyq_extractor.py
```

### Add to PATH (optional, run from anywhere)
```bash
sudo cp pyq_extractor.py /usr/local/bin/pyq-extractor
sudo chmod +x /usr/local/bin/pyq-extractor
# Then just run: pyq-extractor
```

---

## Usage

```
[?] Enter subject name: Computer Networks
```

If exact match found → proceeds directly.

If not found → shows a table:

```
┌──────────────────────────────────────────────────┐
│           Matching Subjects Found                  │
├──┬──────────────────────────┬─────────┬────┬──────┤
│ # │ Subject Name            │ Code    │Year│Match%│
├──┼──────────────────────────┼─────────┼────┼──────┤
│ 1 │ Computer Networks       │ KCS603  │ 3rd│  95% │
│ 2 │ Computer Organization.. │ KCS302  │ 2nd│  72% │
│ 3 │ Computer System Security│ KCS404  │ 2nd│  68% │
└──┴──────────────────────────┴─────────┴────┴──────┘

[?] Select subject number (1-3, or 0 to cancel): 1
```

After confirmation, it downloads all available PYQs.

---

## Supported Subjects (Built-in DB)

| Subject | Code | Year |
|---------|------|------|
| Engineering Mathematics I | BAS103 | 1st |
| Engineering Mathematics II | BAS203 | 1st/2nd |
| Engineering Physics | BAS101 | 1st |
| Engineering Chemistry | BAS102 | 1st |
| Programming for Problem Solving | BCS101 | 1st |
| Data Structures | KCS301 | 2nd |
| Computer Organization & Architecture | KCS302 | 2nd |
| Discrete Mathematics | KAS301 | 2nd |
| TAFL | KCS401 | 2nd |
| OOP | KCS402 | 2nd |
| DBMS | KCS403 | 2nd |
| Operating Systems | KCS501 | 2nd |
| Computer Networks | KCS603 | 3rd |
| DAA | KCS503 | 3rd |
| Software Engineering | KCS601 | 3rd |
| Compiler Design | KCS602 | 3rd |
| Artificial Intelligence | KCS072 | 3rd |
| Machine Learning | KCS073 | 3rd |
| Cloud Computing | KCS074 | 4th |
| Deep Learning | KCS076 | 4th |
| ...and more |

---

## Output Location

```
~/Downloads/
PYQ_Extractor/
Computer_Networks/
KCS603_2022_PYQ.pdf
KCS603_2021_PYQ.pdf
KCS603_2020_PYQ.pdf
...
```

---

## Known Limitations

- Some PDFs may be hosted on Google Drive; those are flagged but require manual download.
- The subject database is pre-built and may not cover all subjects. For unlisted subjects, the tool falls back to a live Google site-search.

---

## Extending the Subject Database

Edit `SUBJECTS_DB` in `pyq_extractor.py`:

```python
"Your Subject Name": {
	"code": "KCSXXX",
	"slug": "url-slug-on-source",  # e.g., "2nd-year-aktu-pyqs-yoursubject"
	"year": "2nd"
},
```

---

## Legal Note

This tool is for **personal educational use only**. PYQ PDFs are freely available on the internet. This tool simply automates the process of finding and downloading them. Do not redistribute scraped content.

---

*"Padhai karo, rank lao."* 🔥
# pyq-notes-extractor
