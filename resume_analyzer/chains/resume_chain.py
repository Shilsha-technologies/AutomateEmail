from __future__ import annotations
import json
import logging
import os
import re
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo
import asyncio

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

from resume_analyzer.schemas import ResumeAnalysisResult

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


@lru_cache(maxsize=1)
def _get_llm() -> ChatGroq:
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1,
        max_tokens=900,
        max_retries=3,
    )



_SYSTEM_PROMPT = """\
You are a senior technical recruiter with 15 years of experience evaluating software engineering resumes.

Your ONLY job is to return a valid JSON object — no markdown, no code fences, no explanation, no preamble.
Any response that is not pure JSON will be rejected.

You must think carefully before assigning each field. Never default, guess, or use placeholder values.
Every field must be derived from the actual resume content provided.
"""

_HUMAN_PROMPT = """\
════════════════════════════════════
CANDIDATE DATA
════════════════════════════════════
Name                : {name}
Email               : {email}
Profile Summary     : {profile_summary}
Skills              : {skills}
Total Experience    : {experience_years}
Work Entries        : {experience_entries}
Education Entries   : {education_count}
Projects            : {projects_count}
Certifications      : {certifications_count}

Resume Text (first 2500 chars):
{raw_text_snippet}

════════════════════════════════════
FIELD-BY-FIELD INSTRUCTIONS
════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD 1 — name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Extract the candidate's REAL full name from the resume text.

STRICT RULES:
  • The "Name" field above is parsed from the PDF header — it is OFTEN WRONG.
    It may contain section headings like "Professional Experience", "Professional Summary",
    "Profile", "About Me", "Objective", etc. — these are NOT names.
  • Read the raw resume text carefully. The real name is almost always:
      – The very first line of the resume, OR
      – A large-font heading at the top, OR
      – Present in the email address (e.g., john.doe@gmail.com → John Doe)
  • A valid name:
      ✓ Contains 2 words (first + last), occasionally 3
      ✓ Each word starts with a capital letter
      ✓ No digits, no special characters
      ✓ Is NOT a section heading or job title
  • If the name truly cannot be determined from any source, return "Unknown Candidate".
  • NEVER return section headings as the name.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD 2 — domain
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Infer the candidate's PRIMARY technical domain from their ENTIRE resume — 
job titles, skills, projects, and profile summary all together.

DETECTION RULES (apply in order, first match wins):

  ── FRONTEND ──────────────────────────────────────────────────────────
  • Primarily React / Redux / Next.js / React Native (web)     → React Developer
  • Primarily Angular / RxJS / NgRx / Angular Material         → Angular Developer
  • Primarily Vue.js / Vuex / Nuxt.js                          → Vue.js Developer
  • Primarily HTML / CSS / SASS / jQuery / Bootstrap (no FW)   → Frontend Developer
  • Primarily React Native / Expo (mobile focus)               → React Native Developer

  ── BACKEND ───────────────────────────────────────────────────────────
  • Primarily Node.js / Express / NestJS (backend focus)       → Node.js Developer
  • Primarily Python / Django / Flask / FastAPI                → Python Developer
  • Primarily Java / Spring / SpringBoot / Hibernate           → Java Developer
  • Primarily C# / .NET / ASP.NET / Entity Framework          → .NET Developer
  • Primarily Go / Golang                                      → Golang Developer
  • Primarily Ruby on Rails                                    → Ruby on Rails Developer
  • Primarily PHP / Laravel / Symfony                         → PHP Developer

  ── FULL STACK ────────────────────────────────────────────────────────
  • Equal React + Node, MERN / MEAN / MEVN stack              → Full Stack Developer
  • Next.js + Node.js / Prisma with equal frontend+backend    → Full Stack Developer
  • SDE Intern with MERN / MEAN / full-stack projects          → Full Stack Developer

  ── MOBILE ────────────────────────────────────────────────────────────
  • Primarily Flutter / Dart                                   → Flutter Developer
  • Primarily Swift / SwiftUI / Xcode / iOS SDK               → iOS Developer
  • Primarily Kotlin / Jetpack Compose / Android SDK           → Android Developer

  ── DATA & AI ─────────────────────────────────────────────────────────
  • Primarily ML / TensorFlow / PyTorch / Scikit-learn / NLP  → Machine Learning Engineer
  • Primarily LLMs / LangChain / RAG / Prompt Engineering     → AI/ML Engineer
  • Primarily Tableau / Power BI / Looker / data analysis     → Data Analyst
  • Primarily Spark / Hadoop / Airflow / ETL pipelines         → Data Engineer
  • Primarily statistics / R / Python (analysis + modeling)   → Data Scientist

  ── DEVOPS & CLOUD ────────────────────────────────────────────────────
  • Primarily Docker / Kubernetes / Terraform / CI-CD         → DevOps Engineer
  • Primarily AWS / GCP / Azure architecture and services     → Cloud Engineer
  • Primarily security / penetration testing / compliance     → Security Engineer

  ── DESIGN ────────────────────────────────────────────────────────────
  • Primarily Figma / Adobe XD / Sketch / UI/UX               → UI/UX Designer

  ── FALLBACK ──────────────────────────────────────────────────────────
  • No detectable tech pattern                                → General

HARD RULES:
  • Analyze the FULL resume text, not just the skills list.
  • Do NOT assign a domain based on one minor library mention.
  • A candidate listing Python + ML/TensorFlow/PyTorch is NOT a "Python Developer" — they are a "Machine Learning Engineer".
  • A candidate listing Angular as a primary skill is NOT a "React Developer".
  • Always prefer the most specific and accurate domain.
  • Never return "General" if any tech pattern is detectable.

Examples of WRONG vs CORRECT domain assignment:
  ✗ WRONG : Skills=[Angular, Python, ML, SQL]         → React Developer
  ✓ RIGHT : Skills=[Angular, Python, ML, SQL]         → Machine Learning Engineer (ML is primary stack)

  ✗ WRONG : Skills=[React, Node.js, Express, MongoDB] → React Developer
  ✓ RIGHT : Skills=[React, Node.js, Express, MongoDB] → Full Stack Developer (equal frontend+backend)

  ✗ WRONG : Skills=[Python, Django, FastAPI, NumPy]   → Data Scientist
  ✓ RIGHT : Skills=[Python, Django, FastAPI, NumPy]   → Python Developer (backend focus)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD 3 — skills
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
List the top 10–20 technical skills extracted from the resume.

RULES:
  • Use exact short professional names: "React.js", "Node.js", "Redux", "NestJS", "AWS", "PostgreSQL"
  • PRIORITIZE domain-relevant skills first, then supporting skills
  • Exclude soft skills ("Communication", "Teamwork", "Leadership") UNLESS the resume is non-technical
  • Exclude vague items like "Problem Solving", "SDLC", "Agile" unless specifically technical
  • Return as a JSON array of strings

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD 4 — level
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Determine seniority level based ONLY on the experience_years value above:

  Fresher   = 0–1 year    (includes internships < 1 year, 0 months)
  Mid-Level = 2–4 years
  Senior    = 5+ years

Return exactly one of: "Fresher", "Mid-Level", "Senior"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD 5 — score  ← CALCULATE THIS CAREFULLY, NEVER DEFAULT TO 50
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Score the candidate from 0–100 using this rubric. Think step by step.

  ┌─────────────────────────────────────────────────┬──────────┐
  │ CATEGORY                                        │ MAX PTS  │
  ├─────────────────────────────────────────────────┼──────────┤
  │ A. Skills relevance to detected domain          │   30 pts │
  │ B. Work experience quality & depth              │   30 pts │
  │ C. Education background                         │   20 pts │
  │ D. Projects + Certifications                    │   20 pts │
  └─────────────────────────────────────────────────┴──────────┘

  CATEGORY A — Skills (0–30):
    25–30 : 8+ highly relevant domain skills, advanced stack
    18–24 : 5–7 relevant domain skills, solid coverage
    10–17 : 3–4 relevant skills, some gaps
     0–9  : Mostly irrelevant or fewer than 3 domain skills

  CATEGORY B — Work Experience (0–30):
    25–30 : 5+ years at reputable companies, senior roles
    18–24 : 2–4 years, relevant job titles, good progression
    10–17 : <2 years, internships only, or unrelated roles
     0–9  : No work experience or completely unrelated

  CATEGORY C — Education (0–20):
    17–20 : Tier-1 university (IIT, NIT, BITS, top global), CS/Engineering degree
    12–16 : Good university, relevant degree (CS, IT, ECE, MCA)
     6–11 : Average college, semi-relevant degree
     0–5  : Unknown institution, unrelated degree, or no education listed

  CATEGORY D — Projects + Certifications (0–20):
    17–20 : 4+ strong domain-relevant projects AND 2+ certifications
    12–16 : 2–3 solid projects OR strong certifications
     6–11 : 1 project OR 1 certification
     0–5  : No projects and no certifications

  EXAMPLES of expected scores:
    • 6-yr Senior Node.js dev, IIT grad, 5 projects, 3 certs    → 88–95
    • 3-yr Mid React dev, good university, 3 projects, 1 cert   → 65–75
    • 10-month Fresher, relevant skills, 2 projects, no cert    → 45–58
    • 0-month Fresher, weak skills, 1 project, no cert          → 25–38

  NEVER return 50 as a default. Always compute the actual score.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD 6 — summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Write exactly ONE professional sentence, 15–25 words.

Format: "<Role> with <exp_label> of experience in <top 2–3 DOMAIN-RELEVANT skills>."

RULES:
  • Use EXACTLY this experience label (do not paraphrase): {exp_label}
  • Skills in the summary MUST be the most relevant to the domain, NOT just the first 3 from the skills list
  • Role must match the domain exactly
  • Never use placeholder text

CORRECT examples:
  "React Developer with 3 years of experience in React.js, Redux, and Next.js."
  "Machine Learning Engineer with 6 months of experience in TensorFlow, PyTorch, and Scikit-learn."
  "Full Stack Developer with 2 years of experience in React.js, Node.js, and MongoDB."

WRONG examples (do not do this):
  ✗ "React Developer with 3 years of experience in JWT, Postman, MySQL."   ← irrelevant skills
  ✗ "Python Developer with 0 months of experience in Django, MySQL, Deep Learning."  ← mixed domain skills
  ✗ "React Developer with 10 months of experience in Prisma, DSA, Python." ← non-React skills listed first

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD 7 — filename
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use EXACTLY this format: FirstName_LastName_DomainSlug_{exp_label}.pdf

  • Use the CORRECTED name from Field 1 (not the raw input name)
  • DomainSlug = domain with spaces replaced by underscores (e.g., React_Developer, Node_js_Developer)
  • exp_label = EXACTLY: {exp_label}
  • Underscores only, no spaces, no hyphens

Examples:
  Ariba_Nusra_React_Developer_3Yrs.pdf
  Sakshi_Semwal_Machine_Learning_Engineer_2Months.pdf
  Ankit_Gaur_Node_js_Developer_6Yrs.pdf

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD 8 — folder
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format: Candidates/DomainSlug/
  • DomainSlug MUST exactly match the slug used in the filename
  • Example: Candidates/React_Developer/ or Candidates/Machine_Learning_Engineer/

════════════════════════════════════

{format_instructions}
"""


def _format_exp(exp_years: float) -> str:
    if exp_years < 1.0:
        months = round(exp_years * 12)
        return f"{months}Months" if months > 0 else "0Months"
    return f"{int(exp_years)}Yrs"


def _format_exp_text(exp_years: float) -> str:
    if exp_years < 1.0:
        months = round(exp_years * 12)
        return f"{months} month{'s' if months != 1 else ''}"
    yrs = int(exp_years)
    return f"{yrs} year{'s' if yrs != 1 else ''}"



def _build_chain():
    parser = JsonOutputParser(pydantic_object=ResumeAnalysisResult)
    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        ("human", _HUMAN_PROMPT),
    ])
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    return prompt | _get_llm() | parser


_chain = None


def _get_chain():
    global _chain
    if _chain is None:
        _chain = _build_chain()
    return _chain


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
        "%Y-%m",
        "%b %Y",
        "%B %Y",
        "%m/%Y",
        "%b-%Y",
        "%B-%Y",
        "%Y",
        "%b %d, %Y",
        "%d %b %Y",
        "%Y-%m-%d",
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
        end = _parse_date(str(ed_raw)) if ed_raw else now

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
    result = round(total_days / 365.25, 1)
    log.info("[EXP] Total: %.1f years from %d merged intervals", result, len(merged))
    return result


def _calculate_exp_years_from_parsed(parsed: dict) -> float:
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
    safe_name = _slugify(name) or "Candidate"
    domain_slug = _slugify(domain)
    exp_str = _format_exp(exp_years)
    return f"{safe_name}_{domain_slug}_{exp_str}.pdf"


def _build_folder(domain: str) -> str:
    return f"Candidates/{_slugify(domain)}/"


def _build_chain_input(parsed: dict, exp_years: float) -> dict:
    name = (parsed.get("name") or "Candidate").strip()
    email = parsed.get("email") or ""
    skills = parsed.get("skills") or []

    work_exp = parsed.get("work_experiences") or []
    work_exp = [e for e in work_exp if isinstance(e, dict)]
    if not work_exp:
        work_exp = [e for e in (parsed.get("experience") or []) if isinstance(e, dict)]

    raw_text = (parsed.get("raw_text") or "")[:2500]
    profile_summary = parsed.get("summary") or parsed.get("profile") or raw_text[:300]

    return {
        "name": name,
        "email": email,
        "profile_summary": profile_summary,
        "skills": ", ".join(str(s) for s in skills[:25]),
        "experience_years": _format_exp_text(exp_years),
        "exp_label": _format_exp(exp_years),
        "experience_entries": len(work_exp),
        "education_count": len(parsed.get("education") or []),
        "projects_count": len(parsed.get("projects") or []),
        "certifications_count": len(parsed.get("certifications") or []),
        "raw_text_snippet": raw_text,
        "example_domains": "\n".join(f"     • {d}" for d in EXAMPLE_DOMAINS),
    }


def _rule_based_fallback(parsed: dict) -> dict:
    exp_years = _calculate_exp_years_from_parsed(parsed)

    raw_text = (parsed.get("raw_text") or json.dumps(parsed)).lower()
    name = (parsed.get("name") or "Candidate").strip()
    skills = [str(s) for s in (parsed.get("skills") or [])[:10]]

    hints = {
        "React Developer": ["react", "redux", "next.js"],
        "Node.js Developer": ["node.js", "nodejs", "nestjs"],
        "Python Developer": ["python", "django", "flask", "fastapi"],
        "Java Developer": ["java", "spring"],
        "Full Stack Developer": ["mern", "mean", "full stack", "fullstack"],
        "Machine Learning Engineer": ["machine learning", "tensorflow", "pytorch"],
        "Data Analyst": ["tableau", "power bi", "data analysis"],
        "DevOps Engineer": ["docker", "kubernetes", "terraform"],
        "UI/UX Designer": ["figma", "wireframe", "ux"],
        "Flutter Developer": ["flutter", "dart"],
        "QA Engineer": ["selenium", "cypress", "playwright"],
        "HR": ["recruitment", "talent acquisition"],
    }

    best_domain, best_score = "General", 0
    for domain, kws in hints.items():
        score = sum(1 for kw in kws if kw in raw_text)
        if score > best_score:
            best_domain, best_score = domain, score

    top_skills = ", ".join(skills[:3]) or "relevant technologies"

    return {
        "domain": best_domain,
        "skills": skills,
        "level": _level(exp_years),
        "score": 50.0,
        "summary": f"{best_domain} with {_format_exp_text(exp_years)} of experience in {top_skills}.",
        "filename": _build_filename(name, best_domain, exp_years),
        "folder": _build_folder(best_domain),
    }


async def run_chain(parsed_resume: dict) -> dict:
    exp_years = _calculate_exp_years_from_parsed(parsed_resume)

    try:
        chain_input = _build_chain_input(parsed_resume, exp_years)
        result = await asyncio.to_thread(_get_chain().invoke, chain_input)

        domain = (result.get("domain") or "General").strip()
        name = (parsed_resume.get("name") or "Candidate").strip()

        result["domain"] = domain
        result["filename"] = _build_filename(name, domain, exp_years)
        result["folder"] = _build_folder(domain)

        summary = result.get("summary", "")
        if not summary or len(summary) < 20 or "john doe" in summary.lower():
            skills_list = result.get("skills") or []
            top_skills = ", ".join(str(s) for s in skills_list[:3]) or "relevant technologies"
            result["summary"] = (
                f"{domain} with {_format_exp_text(exp_years)} of experience in {top_skills}."
            )

        return result

    except Exception as exc:
        log.error("[CHAIN] LLM failed (%s: %s) — using fallback", type(exc).__name__, exc)
        return _rule_based_fallback(parsed_resume)