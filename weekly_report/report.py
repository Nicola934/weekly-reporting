from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from .kpis import KPIResult, kpi_to_dict 
# This function converts a KPIResult object into a dictionary format.
# It imports both the KPIResult class and the kpi_to_dict function from the kpis module located in the same package.


@dataclass(frozen=True)
class ReportArtifacts:
    run_stamp: str
    cleaned_csv: Optional[str]
    kpi_json: Optional[str]
    file_summary_csv: str



def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S") # Returns a timestamp string formatted as "YYYYMMDD_HHMMSS"

def write_reports(
    output_dir: Path, # Accepts a Path object representing the output directory
    basename: str, # Accepts a string representing the base name for the report files
    combined_df: pd.DataFrame, # Accepts a pandas DataFrame containing the cleaned and combined data
    file_summaries: pd.DataFrame, # Accepts a pandas DataFrame containing the file summaries
    kpis: KPIResult, # Accepts a KPIResult object containing the computed KPIs
    write_cleaned_csv: bool, # Accepts a boolean indicating whether to write the cleaned CSV file
    write_kpi_json: bool, # Accepts a boolean indicating whether to write the KPI JSON file
) -> ReportArtifacts: # Returns a ReportArtifacts object containing paths to the generated report files
    output_dir.mkdir(parents=True, exist_ok=True) # Ensures that the output directory exists; if not, it creates it along with any necessary parent directories
    stamp = _stamp() # Stores the current timestamp in the variable stamp

    file_summary_path = output_dir / f"{basename}_file_summary_{stamp}.csv"
    file_summaries.to_csv(file_summary_path, index=False)# Writes the file summaries DataFrame to a CSV file in the output directory with a timestamped filename

    cleaned_csv_path = None
    if write_cleaned_csv: # If the write_cleaned_csv flag is True, it writes the cleaned and combined DataFrame to a CSV file
        cleaned_csv_path = output_dir / f"{basename}_cleaned_{stamp}.csv" # Constructs the path for the cleaned CSV file with a timestamped filename
        combined_df.to_csv(cleaned_csv_path, index=False) # Writes the combined DataFrame to the cleaned CSV file without including the index

    kpi_json_path = None
    if write_kpi_json:
        kpi_json_path = output_dir / f"{basename}_kpis_{stamp}.json"
        kpi_json_path.write_text(json.dumps(kpi_to_dict(kpis), indent=2), encoding="utf-8")


    return ReportArtifacts(
        run_stamp=stamp,
        cleaned_csv=str(cleaned_csv_path) if cleaned_csv_path else None,
        kpi_json=str(kpi_json_path) if kpi_json_path else None,
        file_summary_csv=str(file_summary_path),
    )