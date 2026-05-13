from __future__ import annotations
import json
import logging
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio

from groq import Groq

# ── Commented out: Ollama / LangChain imports ──────────────────
# from functools import lru_cache
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.messages import SystemMessage, HumanMessage
# from langchain_ollama import ChatOllama
# from resume_analyzer.schemas import ResumeAnalysisResult
# ──────────────────────────────────────────────────────────────

log = logging.getLogger(__name__)

EXAMPLE_DOMAINS: list[str] = [
    "Python Developer",
    "React Developer",
    "Java Developer",
    "Node.js Developer",
    "Angular Developer",
    "Vue.js Developer",
    "Full Stack Developer",
    "Flutter Developer",
    "Android Developer",
    "iOS Developer",
    "Data Analyst",
    "Data Scientist",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "UI/UX Designer",
    "QA Engineer",
    "HR",
    "Blockchain Developer",
    "Embedded Systems Engineer",
    "Cybersecurity Engineer",
    "Game Developer",
]


# ── Commented out: Ollama LLM ──────────────────────────────────
# @lru_cache(maxsize=1)
# def _get_llm() -> ChatOllama:
#     return ChatOllama(
#         model="qwen2.5:3b",
#         temperature=0.1,
#         num_predict=300,
#         timeout=120,
#     )
# ──────────────────────────────────────────────────────────────

# ── Groq client ────────────────────────────────────────────────
_groq_client = None

def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client


def _call_groq(chain_input: dict) -> dict:
    prompt = _HUMAN_PROMPT.format(**chain_input)

    response = _get_groq_client().chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=400,
        temperature=0.1,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
    )

    content = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    content = re.sub(r'^```json\s*', '', content)
    content = re.sub(r'\s*```$',     '', content)

    return json.loads(content)
# ──────────────────────────────────────────────────────────────


_SYSTEM_PROMPT = """You are an expert ATS resume evaluation system and senior technical recruiter.

Return ONLY valid JSON.
Do not return markdown.
Do not return explanations.
Do not return code fences.
Do not return additional text.

Every field must be derived strictly from the resume data provided.
Never guess unavailable information.
"""

_HUMAN_PROMPT = """CANDIDATE DATA

Name: {name}
Email: {email}
Experience: {experience_years}
Profile Summary: {profile_summary}

Pre-extracted Skills (USE THESE — already verified from resume):
{skills}

Work Experience entries: {experience_entries}
Projects count: {projects_count}
Education count: {education_count}
Certifications count: {certifications_count}

==================================================
RAW RESUME TEXT (PRIMARY SOURCE OF TRUTH)
==================================================

{raw_text_snippet}

==================================================
IMPORTANT RAW TEXT RULES
==================================================

The raw resume text above is the PRIMARY SOURCE OF TRUTH.

Use the raw resume text to:
- understand the candidate's actual role/domain
- identify technologies and project context
- understand education/work/project relevance
- determine specialization accurately

The structured fields above (skills, experience, counts)
are already pre-validated and extracted from the same resume.

IMPORTANT:
- Never invent information not present in the raw resume text.
- Prefer evidence from the raw resume text over assumptions.
- Use the raw text context to choose the MOST accurate domain.

If skills and raw resume context conflict,
prefer the raw resume project/work experience context.

==================================================
TASKS
==================================================

1. Detect the SINGLE most suitable technical domain.
2. Select top domain-relevant skills FROM the pre-extracted skills list above only.
3. Determine seniority level.
4. Calculate ATS score.
5. Generate professional one-line summary.
6. Generate filename.
7. Generate folder path.

==================================================
DOMAIN DETECTION RULES
==================================================

Do NOT classify candidate only from skills list.
Use projects, work experience, and resume context from raw text.

Frontend:
- React / Redux / Next.js → React Developer
- Angular / NgRx / RxJS → Angular Developer
- Vue.js / Nuxt.js → Vue.js Developer

Backend:
- Python / Django / Flask / FastAPI → Python Developer
- Node.js / Express / NestJS → Node.js Developer
- Java / Spring Boot → Java Developer
- PHP / Laravel → PHP Developer
- C# / .NET → .NET Developer

Full Stack:
- MERN / MEAN / React + Node.js equally → Full Stack Developer

Mobile:
- Flutter / Dart → Flutter Developer
- Kotlin / Android SDK → Android Developer
- Swift / SwiftUI → iOS Developer

Data & AI:
- TensorFlow / PyTorch / NLP / ML → Machine Learning Engineer
- LangChain / RAG / LLMs → AI/ML Engineer
- Power BI / Tableau / Analytics → Data Analyst
- Spark / Hadoop / Airflow / ETL → Data Engineer
- Statistics / Modeling / Research → Data Scientist

DevOps & Cloud:
- Docker / Kubernetes / CI-CD → DevOps Engineer
- AWS / Azure / GCP Architecture → Cloud Engineer
- Security / PenTesting → Security Engineer

Design:
- Figma / UI / UX → UI/UX Designer

Fallback:
- No strong pattern → General

IMPORTANT:
- Use ENTIRE resume context.
- Prefer the MOST specialized matching domain.
- Do NOT classify based on one minor skill mention.

==================================================
LEVEL RULES
==================================================

0 to 1 year   → Fresher
2 to 4 years  → Mid-Level
5+ years      → Senior

Use the Experience field above as the primary source for years.

==================================================
ATS SCORING RULES
==================================================

Score candidate from 0-100 using:

A. Skills Relevance         → 30
B. Work Experience          → 30
C. Education                → 20
D. Projects/Certifications → 20

Guidelines:
- Strong domain alignment increases score
- Strong projects improve score
- Relevant experience improves score
- Weak or unrelated resumes reduce score
- Never default to 50

==================================================
SUMMARY RULES
==================================================

Write EXACTLY one sentence:

"<Domain> with <experience from the Experience field above> of experience in <top 2-3 relevant skills>."

Examples:
- React Developer with 2 years 9 months of experience in React.js, Redux, and Next.js.
- Machine Learning Engineer with 6 months of experience in TensorFlow, PyTorch, and Scikit-learn.
- Java Developer with 6 months of experience in Spring Boot, MySQL, and REST APIs.

IMPORTANT: Use the exact experience text provided in the Experience field. Do not invent or change it.

==================================================
FILENAME RULES
==================================================

Format: FirstName_LastName_DomainSlug_ExpLabel.pdf

ExpLabel examples: 2Yrs9Mon, 6Mon, 3Yrs, Fresher (if 0 experience)

Examples:
- Shubhav_Kumar_React_Developer_2Yrs9Mon.pdf
- Abhay_Rana_Machine_Learning_Engineer_6Mon.pdf
- Vishwas_Maurya_Java_Developer_6Mon.pdf

==================================================
FOLDER RULES
==================================================

Format: Candidates/DomainSlug/

==================================================
OUTPUT REQUIREMENTS
==================================================

Return ONLY valid JSON matching this schema exactly:

{{
  "name":"string",
  "domain": "string",
  "skills": ["string"],
  "level": "string",
  "score": 0,
  "summary": "string",
  "filename": "string",
  "folder": "string"
}}

IMPORTANT:
- skills must be chosen FROM the pre-extracted skills list above only
- score must be between 0 and 100
- Return ONLY the JSON object, nothing else
"""


def _format_exp_label(exp_years: float) -> str:
    if exp_years is None or exp_years == 0.0:
        return "Fresher"
    total_months = round(exp_years * 12)
    years  = total_months // 12
    months = total_months % 12
    if years and months:
        return f"{years}Yrs{months}Mon"
    elif years:
        return f"{years}Yrs"
    else:
        return f"{months}Mon"


def _format_exp_text(exp_years: float) -> str:
    if exp_years is None or exp_years == 0.0:
        return "0 months"
    total_months = round(exp_years * 12)
    years  = total_months // 12
    months = total_months % 12
    if years and months:
        return f"{years} year{'s' if years != 1 else ''} {months} month{'s' if months != 1 else ''}"
    elif years:
        return f"{years} year{'s' if years != 1 else ''}"
    else:
        return f"{months} month{'s' if months != 1 else ''}"


# ── Commented out: LangChain chain builder ─────────────────────
# def _build_chain():
#     parser = JsonOutputParser(pydantic_object=ResumeAnalysisResult)
#     prompt = ChatPromptTemplate.from_messages([
#         SystemMessage(content=_SYSTEM_PROMPT),
#         HumanMessage(content=_HUMAN_PROMPT),
#     ])
#     prompt = prompt.partial(format_instructions=parser.get_format_instructions())
#     return prompt | _get_llm() | parser
#
# _chain = None
#
# def _get_chain():
#     global _chain
#     if _chain is None:
#         _chain = _build_chain()
#     return _chain
# ──────────────────────────────────────────────────────────────

def _parse_date(raw: str) -> datetime | None:
    if not raw:
        return None
    s = raw.strip()
    if s.lower() in ("present", "current", "till date", "ongoing", "now", ""):
        return datetime.now(ZoneInfo("Asia/Kolkata"))

    s = re.sub(
        r'^([A-Za-z]+)\s+(\d{2})$',
        lambda m: f"{m.group(1)} {2000 + int(m.group(2))}",
        s
    )

    formats = [
        "%Y-%m", "%b %Y", "%B %Y", "%m/%Y", "%b-%Y",
        "%B-%Y", "%Y", "%b %d, %Y", "%d %b %Y", "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    try:
        from dateutil import parser as dp
        return dp.parse(s, default=datetime(2000, 1, 1))
    except Exception:
        return None


def _calculate_exp_years(work_experiences: list) -> float:
    if not work_experiences:
        return 0.0

    now = datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
    intervals: list[tuple[datetime, datetime]] = []

    for entry in work_experiences:
        if not isinstance(entry, dict):
            continue

        sd_raw = (
            entry.get("startDate") or entry.get("start_date") or
            entry.get("from") or ""
        )
        ed_raw = (
            entry.get("endDate") or entry.get("end_date") or
            entry.get("to") or "present"
        )

        if not sd_raw:
            log.warning("[EXP] Skipping entry with no startDate: %s", entry)
            continue

        start = _parse_date(str(sd_raw))
        end   = _parse_date(str(ed_raw)) if ed_raw else now

        if start is None:
            log.warning("[EXP] Could not parse startDate: %r", sd_raw)
            continue
        if end is None:
            end = now

        if hasattr(start, "tzinfo") and start.tzinfo:
            start = start.replace(tzinfo=None)
        if hasattr(end, "tzinfo") and end.tzinfo:
            end = end.replace(tzinfo=None)

        end = min(end, now)

        if end > start:
            intervals.append((start, end))
        else:
            log.warning("[EXP] Skipping invalid interval: %s → %s", start, end)

    if not intervals:
        return 0.0

    intervals.sort(key=lambda x: x[0])
    merged: list[tuple[datetime, datetime]] = [intervals[0]]
    for s, e in intervals[1:]:
        if s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    total_days = sum((e - s).days for s, e in merged)
    result = round(total_days / 365.25, 2)
    log.info("[EXP] Total: %.2f years from %d merged intervals", result, len(merged))
    return result


def _calculate_exp_years_from_parsed(parsed: dict) -> float:
    pre = parsed.get("exp_years")
    if pre is not None:
        log.info("[EXP] Using pre-extracted exp_years: %.2f", pre)
        return float(pre)

    work_exp = parsed.get("work_experiences") or []
    work_exp = [e for e in work_exp if isinstance(e, dict) and e.get("startDate")]
    if work_exp:
        return _calculate_exp_years(work_exp)

    llm_exp = parsed.get("experience") or []
    llm_exp = [e for e in llm_exp if isinstance(e, dict) and e.get("startDate")]
    if llm_exp:
        return _calculate_exp_years(llm_exp)

    return 0.0


def _slugify(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")


def _level(exp_years: float) -> str:
    if exp_years < 1:
        return "Fresher"
    if exp_years <= 4:
        return "Mid-Level"
    return "Senior"


def _build_filename(name: str, domain: str, exp_years: float) -> str:
    safe_name   = _slugify(name) or "Candidate"
    domain_slug = _slugify(domain)
    exp_label   = _format_exp_label(exp_years)
    return f"{safe_name}_{domain_slug}_{exp_label}.pdf"


def _build_folder(domain: str) -> str:
    return f"Candidates/{_slugify(domain)}/"


def _build_chain_input(parsed: dict, exp_years: float) -> dict:
    name  = (parsed.get("name") or "Candidate").strip()
    email = parsed.get("email") or ""
    skills = parsed.get("skills") or []

    work_exp = parsed.get("work_experiences") or []
    work_exp = [e for e in work_exp if isinstance(e, dict)]
    if not work_exp:
        work_exp = [e for e in (parsed.get("experience") or []) if isinstance(e, dict)]

    raw_text = (parsed.get("raw_text") or "")[:2500]
    profile_summary = parsed.get("summary") or parsed.get("profile") or raw_text[:300]

    return {
        "name":                 name,
        "email":                email,
        "profile_summary":      profile_summary,
        "skills":               ", ".join(str(s) for s in skills),
        "experience_years":     _format_exp_text(exp_years),
        "exp_label":            _format_exp_label(exp_years),
        "experience_entries":   len(work_exp),
        "education_count":      len(parsed.get("education") or []),
        "projects_count":       len(parsed.get("projects") or []),
        "certifications_count": len(parsed.get("certifications") or []),
        "raw_text_snippet":     raw_text,
        "example_domains":      "\n".join(f"     • {d}" for d in EXAMPLE_DOMAINS),
    }


def _rule_based_fallback(parsed: dict) -> dict:
    exp_years = _calculate_exp_years_from_parsed(parsed)
    raw_text  = (parsed.get("raw_text") or json.dumps(parsed)).lower()
    name      = (parsed.get("name") or "Candidate").strip()
    skills    = [str(s) for s in (parsed.get("skills") or [])]

    hints = {
        "React Developer":           ["react", "redux", "next.js"],
        "Node.js Developer":         ["node.js", "nodejs", "nestjs"],
        "Python Developer":          ["python", "django", "flask", "fastapi"],
        "Java Developer":            ["java", "spring"],
        "Full Stack Developer":      ["mern", "mean", "full stack", "fullstack"],
        "Machine Learning Engineer": ["machine learning", "tensorflow", "pytorch"],
        "Data Analyst":              ["tableau", "power bi", "data analysis"],
        "DevOps Engineer":           ["docker", "kubernetes", "terraform"],
        "UI/UX Designer":            ["figma", "wireframe", "ux"],
        "Flutter Developer":         ["flutter", "dart"],
        "QA Engineer":               ["selenium", "cypress", "playwright"],
        "HR":                        ["recruitment", "talent acquisition"],
    }

    best_domain, best_score = "General", 0
    for domain, kws in hints.items():
        score = sum(1 for kw in kws if kw in raw_text)
        if score > best_score:
            best_domain, best_score = domain, score

    top_skills = ", ".join(skills[:3]) or "relevant technologies"

    return {
        "name":       name,
        "email":      parsed.get("email") or "",
        "domain":     best_domain,
        "skills":     skills,
        "level":      _level(exp_years),
        "score":      50,
        "summary":    f"{best_domain} with {_format_exp_text(exp_years)} of experience in {top_skills}.",
        "filename":   _build_filename(name, best_domain, exp_years),
        "folder":     _build_folder(best_domain),
        "confidence": 40,
    }


async def run_chain(parsed_resume: dict) -> dict:
    exp_years = _calculate_exp_years_from_parsed(parsed_resume)
    log.info("[CHAIN] exp_years=%.2f for candidate=%s", exp_years, parsed_resume.get("name"))

    pre_extracted_skills = parsed_resume.get("skills") or []
    name = (parsed_resume.get("name") or "Candidate").strip()

    try:
        chain_input = _build_chain_input(parsed_resume, exp_years)

        # ── Commented out: Ollama call ─────────────────────────
        # result = await asyncio.wait_for(
        #     asyncio.to_thread(_get_chain().invoke, chain_input),
        #     timeout=120
        # )
        # ──────────────────────────────────────────────────────

        # ── Groq API call ──────────────────────────────────────
        result = await asyncio.wait_for(
            asyncio.to_thread(_call_groq, chain_input),
            timeout=30
        )
        # ──────────────────────────────────────────────────────

        domain = (result.get("domain") or "General").strip()

        result["name"]     = name
        result["email"]    = parsed_resume.get("email") or result.get("email") or ""
        result["domain"]   = domain
        result["filename"] = _build_filename(name, domain, exp_years)
        result["folder"]   = _build_folder(domain)
        result["level"]    = result.get("level") or _level(exp_years)

        llm_skills = result.get("skills") or []
        if not llm_skills or llm_skills == ["string"]:
            result["skills"] = pre_extracted_skills
        else:
            pre_lower = {s.lower() for s in pre_extracted_skills}
            filtered  = [s for s in llm_skills if s.lower() in pre_lower]
            result["skills"] = filtered if filtered else pre_extracted_skills

        summary = result.get("summary", "")
        if not summary or len(summary) < 20 or "john doe" in summary.lower():
            top_skills = ", ".join(str(s) for s in result["skills"][:3]) or "relevant technologies"
            result["summary"] = (
                f"{domain} with {_format_exp_text(exp_years)} of experience in {top_skills}."
            )

        return result

    except asyncio.TimeoutError:
        log.error("[CHAIN] Groq timed out — using fallback")
        return _rule_based_fallback(parsed_resume)
    except Exception as exc:
        log.error("[CHAIN] Groq failed (%s: %s) — using fallback", type(exc).__name__, exc)
        return _rule_based_fallback(parsed_resume)