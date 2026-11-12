"""Dataset consolidation service replacing legacy merge_data.py."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.config import LoggingConfig


class DataMergerService:
    REQUIRED_COLS = ["Movement", "Finger", "C0", "C1", "C2", "C3"]
    OUTPUT_COLS = ["Movement", "Finger", "Phalange", "Avg", "Min", "Max"]

    def __init__(self, config: LoggingConfig) -> None:
        self._config = config

    def merge_directory(
        self,
        folder_path: Optional[Path] = None,
        output_csv_path: Optional[Path] = None,
    ) -> Tuple[bool, str, int]:
        """
        Reads all .xlsx/.xls files from folder_path, computes Avg/Min/Max
        per (Movement, Finger, Phalange) and exports semicolon-separated CSV.
        Returns: (success, message, processed_files_count)
        """
        target_dir = folder_path or Path(self._config.data_dir)
        if not target_dir.exists() or not target_dir.is_dir():
            return False, f"Directory '{target_dir}' not found.", 0

        out_path = output_csv_path or (target_dir / self._config.merged_output_filename)
        all_dfs: List[pd.DataFrame] = []
        file_count = 0

        for file in sorted(target_dir.iterdir()):
            if file.is_file() and file.suffix.lower() in (".xlsx", ".xls"):
                try:
                    df = pd.read_excel(file)
                    df.columns = df.columns.str.strip()
                    if all(col in df.columns for col in self.REQUIRED_COLS):
                        all_dfs.append(df)
                        file_count += 1
                except Exception:
                    continue

        if file_count == 0:
            return False, "No valid Excel file found for consolidation.", 0

        full_df = pd.concat(all_dfs, ignore_index=True)
        for col in ("C0", "C1", "C2", "C3"):
            full_df[col] = pd.to_numeric(full_df[col], errors="coerce")

        results: List[Dict[str, object]] = []
        grouped = full_df.groupby(["Movement", "Finger"])

        for (movement, finger), group in grouped:
            mvmt_check = str(movement).strip().lower()
            if mvmt_check in ("push", "pull"):
                vals = group["C3"].dropna()
                if not vals.empty:
                    results.append({
                        "Movement": movement,
                        "Finger": finger,
                        "Phalange": "-",
                        "Avg": f"{vals.mean():.2f}",
                        "Min": f"{vals.min():.2f}",
                        "Max": f"{vals.max():.2f}",
                    })
            else:
                sensor_map = {1: "C0", 2: "C1", 3: "C2"}
                for phalange_num, col_name in sensor_map.items():
                    vals = group[col_name].dropna()
                    if not vals.empty:
                        results.append({
                            "Movement": movement,
                            "Finger": finger,
                            "Phalange": phalange_num,
                            "Avg": f"{vals.mean():.2f}",
                            "Min": f"{vals.min():.2f}",
                            "Max": f"{vals.max():.2f}",
                        })

        if not results:
            return False, "Files were read, but no valid numeric rows were found.", file_count

        result_df = pd.DataFrame(results)[self.OUTPUT_COLS]
        result_df.to_csv(out_path, sep=";", index=False)
        return True, f"Success! {file_count} spreadsheet(s) consolidated into '{out_path.name}'.", file_count
