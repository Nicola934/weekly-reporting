from __future__ import annotations

import logging
import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage # For creating email messages. email.message is a module in the Python standard library that provides classes and functions for creating and manipulating email messages.
from typing import List, Optional
from pathlib import Path

from .config import EmailConfig
from .kpis import KPIResult

logger = logging.getLogger(__name__)


def _get_env(name: str) -> str:

    v = os.getenv(name) 

    if not v:
        raise RuntimeError(f"Missing required environment vairable: {name}")
    return v

def send_report_email(
    email_cfg: EmailConfig, # Configuration for sending the email coming from config.py
    kpis: KPIResult, # KPI results coming from kpis.py 
    attachments: List[Path], # List of file paths to attach to the email coming from report.py
    dry_run: bool = False,
) -> None:
    """
    Uses SMTP with credentials from env vars:
        REPORT_SMTP_USER
        REPORT_SMTP_PASS

    For Gmail you likely need an App Password (not your normal password).
    """
    if not email_cfg.enabled:
        logger.info("Email disabled in config. Skipping send.")
        return

    subject = f"{email_cfg.subject_prefix} Total={kpis.total_responses}"
    body_lines = [
        "Weekly Auto-Report",
        "",
        f"Total responses: {kpis.total_responses}",
    ]
    if kpis.total_responses:
        body_lines +=[
            f"Satisfaction rate: {kpis.satisfaction_rate *100:.1f}%" if kpis.satisfaction_rate is not None else "Satisfaction rate: N/A",
            f"Recommendation rate: {kpis.recommendation_rate * 100:.1f}%" if kpis.recommendation_rate is not None else "Recommendation rate: N/A",
            f"Most used service: {kpis.most_used_service}",
            f"Top region: {kpis.top_region}",
        ]
    body = "\n".join(body_lines)

    msg = EmailMessage() 
    msg["From"] = email_cfg.from_addr
    msg["To"] = ", ".join(email_cfg.to_addrs)
    msg["Subject"] = subject
    msg.set_content(body)

    for p in attachments: # attechments is a list of Path objects representing the file paths to attach to the email
        if not p.exists():
            continue
        data = p.read_bytes() # Calculates the size of the file in bytes

        msg.add_attachment(data, maintype="application", subtype="octet-stream", filename=p.name)
        
    if dry_run:
        logger.info("DRY RUN: Email would be prepared with %d attachment(s); no network connection.", len(attachments))
        return

    smtp_user = _get_env("REPORT_SMTP_USER")
    smtp_pass = _get_env("REPORT_SMTP_PASS")

    logger.info("Sending email to %s via %s:%s ...", email_cfg.to_addrs, email_cfg.smtp_host, email_cfg.smtp_port)
       
    with smtplib.SMTP(email_cfg.smtp_host, email_cfg.smtp_port, timeout=20) as server:
        if email_cfg.use_starttls:
            server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    logger.info("Email sent.")