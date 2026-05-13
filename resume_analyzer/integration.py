import os
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from resume_analyzer.drive_service import upload_resume, get_mime_type
from resume_analyzer.models import ResumeAnalysis
from services.attachment_reader import process_and_analyze_attachment


async def run_resume_analyzer(
    candidate,
    file_path: str,
    filename:  str,
    provider:  str,
    db:        Session,
) -> None:
    try:
        analysis = await process_and_analyze_attachment(
            file_path      = file_path,
            provider       = provider,
            db             = db,
            candidate_name = candidate.name or "Candidate",
        )

        drive_result = {"file_id": "", "drive_link": ""}
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                drive_result = upload_resume(
                    file_bytes  = file_bytes,
                    filename    = analysis["filename"],
                    folder_path = analysis["folder"],
                    mime_type   = get_mime_type(filename),
                )
            except Exception as drive_err:
                print(f"[DRIVE WARN] Could not upload {filename}: {drive_err}")
        else:
            print(f"[ANALYZER WARN] File not on disk, skipping Drive upload: {file_path}")


        candidate_email = (
            analysis.get("email")
            or getattr(candidate, "email", None)
            or None
        )

        record = ResumeAnalysis(
            candidate_name  = analysis.get("name") or candidate.name or "Unknown",
            candidate_email = candidate_email,
            domain          = analysis["domain"],
            skills          = analysis.get("skills", []),
            level           = analysis["level"],
            score           = analysis["score"],
            summary         = analysis["summary"],
            filename        = analysis["filename"],
            folder_path     = analysis["folder"],
            drive_link      = drive_result["drive_link"],
            drive_file_id   = drive_result["file_id"],
            source          = "email_sync",
            provider        = provider,
            created_at      = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"),
        )
        db.add(record)
        db.commit()

        print(
            f"[ANALYZER] ✓ {record.candidate_name} → {analysis['domain']} | "
            f"Score: {analysis['score']} | {analysis['level']} | "
            f"Email: {candidate_email or '(none)'} | "
            f"Drive: {'✓' if drive_result['drive_link'] else '✗ (skipped)'}"
        )

    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        print(f"[ANALYZER ERROR] Failed for {filename}: {e}")