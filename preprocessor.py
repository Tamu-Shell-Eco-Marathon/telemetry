'''
This script adds additional fields into existing log files
that are not computed or saved by the DIS in order to reduce
DIS logging time
'''

import pandas as pd
import os
from pathlib import Path

# Define the directory containing the logs
SCRIPT_DIR = Path(__file__).parent.absolute()
RAW_LOGS_DIR = SCRIPT_DIR / "logs" / "raw"
FINAL_LOGS_DIR = SCRIPT_DIR / "logs" / "final"

def process_logs():
    """
    Scans the raw logs directory for unprocessed CSV files, adds calculated columns,
    renames them with a 'P' suffix, and moves them to the final directory.
    """
    if not RAW_LOGS_DIR.exists():
        print(f"Raw logs directory not found at: {RAW_LOGS_DIR}")
        return

    # Ensure final directory exists
    FINAL_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # List all CSV files in the raw logs directory
    log_files = list(RAW_LOGS_DIR.glob("*.csv"))

    if not log_files:
        print("No CSV files found in the raw logs directory.")
        return


    for file_path in log_files:
        # 1. Check if file is already processed based on filename
        if file_path.stem.startswith("P_"):
            continue

        print(f"Processing {file_path.name}...")

        try:
            df = pd.read_csv(file_path)

            # 2. Check for whether certain columns exist
            # If the columns already exist, we might want to skip or re-process.
            # ---------------------------------------------------------
            # TODO: Define the columns you expect to see in a processed file
            # expected_cols = ['PowerAccumulated', 'Distance']
            # if all(col in df.columns for col in expected_cols):
            #     print(f"  - Columns already exist. Skipping calculation.")
            # else:
            #     pass # Proceed to calculation
            # ---------------------------------------------------------

            # 3. Perform Calculations / Add Columns
            # ---------------------------------------------------------
            # TODO: Add your custom column calculations here.
            # You can access existing columns like df['Speed'], df['Volts'], etc.
            
            # Example:
            # df['PowerAccumulated'] = df['PowerInst'].cumsum()
            
            
            # ---------------------------------------------------------

            # 4. Save and Rename
            # Prepend 'P_' to the filename to indicate it is processed
            new_filename = f"P_{file_path.stem}{file_path.suffix}"
            new_path = FINAL_LOGS_DIR / new_filename

            df.to_csv(new_path, index=False)
            print(f"  - Saved processed log to: {new_filename}")

            # Remove the original file
            os.remove(file_path)

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

if __name__ == "__main__":
    process_logs()
