"""Regression tests for the analyst portfolio reporting pipeline.

Run with: python -m unittest discover -s tests -v
No email or network requests are sent.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from weekly_report.config import AppConfig, ColumnMap, EmailConfig
from weekly_report.emailer import send_report_email
from weekly_report.ingest import discover_inputs
from weekly_report.kpis import compute_kpis, kpi_to_dict
from weekly_report.processing import clean_df, dedupe_df
from weekly_report.report import write_reports
from weekly_report.pipeline import run_pipeline


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.cm = ColumnMap(
            service_col="Service_Category",
            region_col="Region",
            satisfied_col="Satisfied",
            recommend_col="Recommend",
            date_col="Response_Date",
            respondent_id_col="Respondent_id",
        )

    def test_clean_dedupe_and_json_report(self):
        raw = pd.DataFrame([
            {"Service_Category": " support ", "Region": " north ",
             "Satisfied": "yes", "Recommend": "no",
             "Response_Date": "2026-01-01", "Respondent_id": "1"},
            {"Service_Category": "support", "Region": "north",
             "Satisfied": "yes", "Recommend": "no",
             "Response_Date": "2026-01-01", "Respondent_id": "1"},
            {"Service_Category": "sales", "Region": "south",
             "Satisfied": "no", "Recommend": "yes",
             "Response_Date": "2026-01-02", "Respondent_id": "2"},
        ])
        clean = dedupe_df(clean_df(raw, self.cm), self.cm)
        self.assertEqual(len(clean), 2)
        result = compute_kpis(clean, self.cm)
        self.assertEqual(result.total_responses, 2)
        self.assertEqual(result.satisfaction_rate, 0.5)
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts = write_reports(
                Path(temp_dir), "weekly_report", clean,
                pd.DataFrame([{"filename": "sample.csv", "raw_rows": 3, "clean_rows": 2}]),
                result, True, True,
            )
            payload = json.loads(Path(artifacts.kpi_json).read_text(encoding="utf-8"))
            self.assertEqual(payload, kpi_to_dict(result))
            self.assertEqual(payload["total_responses"], 2)
            self.assertTrue(Path(artifacts.cleaned_csv).is_file())

    def test_csv_glob_discovers_csv_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            (folder / "sample.csv").write_text("a\n1\n", encoding="utf-8")
            self.assertEqual([f.name for f in discover_inputs(folder, ["*.csv"])], ["sample.csv"])

    def test_email_dry_run_never_requires_credentials_or_network(self):
        cfg = EmailConfig(True, "smtp.example.com", 587, True,
                          "sender@example.com", ["recipient@example.com"], "Report")
        kpis = compute_kpis(pd.DataFrame(), self.cm)
        with patch.dict("os.environ", {"REPORT_SMTP_USER": "", "REPORT_SMTP_PASS": ""}):
            with patch("weekly_report.emailer.smtplib.SMTP") as smtp:
                send_report_email(cfg, kpis, [], dry_run=True)
                smtp.assert_not_called()

    def test_smtp_without_starttls_is_rejected_before_connection(self):
        cfg = EmailConfig(True, "smtp.example.com", 587, False,
                          "sender@example.com", ["recipient@example.com"], "Report")
        kpis = compute_kpis(pd.DataFrame(), self.cm)
        with patch("weekly_report.emailer.smtplib.SMTP") as smtp:
            with self.assertRaisesRegex(ValueError, "requires STARTTLS"):
                send_report_email(cfg, kpis, [], dry_run=False)
            smtp.assert_not_called()

    def test_smtp_starttls_authenticates_and_sends(self):
        cfg = EmailConfig(True, "smtp.example.com", 587, True,
                          "sender@example.com", ["recipient@example.com"], "Report")
        kpis = compute_kpis(pd.DataFrame(), self.cm)
        with patch.dict("os.environ", {"REPORT_SMTP_USER": "example", "REPORT_SMTP_PASS": "dummy"}):
            with patch("weekly_report.emailer.smtplib.SMTP") as smtp:
                conn = smtp.return_value.__enter__.return_value
                send_report_email(cfg, kpis, [], dry_run=False)
                conn.starttls.assert_called_once()
                conn.login.assert_called_once_with("example", "dummy")
                conn.send_message.assert_called_once()


    def test_full_synthetic_pipeline_without_email(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cfg = AppConfig(
                inbox_dir=root / "data" / "inbox",
                processed_dir=root / "data" / "processed",
                failed_dir=root / "data" / "failed",
                output_dir=root / "output",
                log_dir=root / "logs",
                input_globs=["*.csv"],
                report_basename="weekly_report",
                write_cleaned_csv=True,
                write_kpi_json=True,
                column_map=self.cm,
                email=EmailConfig(False, "smtp.example.com", 587, True,
                                  "sender@example.com", ["recipient@example.com"], "Report"),
            )
            cfg.ensure_dirs()
            pd.DataFrame([
                {"Service_Category": " support ", "Region": "north",
                 "Satisfied": "yes", "Recommend": "yes",
                 "Response_Date": "2026-11-01", "Respondent_id": "1"},
                {"Service_Category": "support", "Region": "north",
                 "Satisfied": "yes", "Recommend": "yes",
                 "Response_Date": "2026-11-01", "Respondent_id": "1"},
                {"Service_Category": "sales", "Region": "south",
                 "Satisfied": "no", "Recommend": "yes",
                 "Response_Date": "2026-11-02", "Respondent_id": "2"},
            ]).to_csv(cfg.inbox_dir / "sample.csv", index=False)
            with patch("weekly_report.emailer.smtplib.SMTP") as smtp:
                result = run_pipeline(cfg)
                smtp.assert_not_called()
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["inputs_processed"], 1)
            self.assertFalse((cfg.inbox_dir / "sample.csv").exists())
            self.assertTrue((cfg.processed_dir / "sample.csv").is_file())
            self.assertEqual(len(pd.read_csv(result["cleaned_csv"])), 2)
            payload = json.loads(Path(result["kpi_json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["total_responses"], 2)


if __name__ == "__main__":
    unittest.main()
