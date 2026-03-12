import json
import csv
from pathlib import Path
from datetime import datetime

# Input and output paths

DATA_DIR = Path(__file__).parent / "Data"


# Ask for input filename

input_filename = input("Enter JSON filename (in Data/): ").strip()
input_path = DATA_DIR / input_filename
# Set output filename and path
output_filename = Path(input_filename).stem + "_filtered.tsv"
OUTPUT_FILE = input_path.parent / output_filename

# Read JSON data
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract timestamp (hh:mm:ss) and bpm

# Ask for start and end time
start_time_input = input("Enter start time (hh:mm): ").strip()
end_time_input = input("Enter end time (hh:mm): ").strip()
start_time = datetime.strptime(start_time_input + ":00", "%H:%M:%S")
end_time = datetime.strptime(end_time_input + ":00", "%H:%M:%S")

rows = []
for item in data:
    dt_str = item.get("dateTime", "")
    try:
        dt = datetime.strptime(dt_str, "%m/%d/%y %H:%M:%S")
        timestamp = dt.strftime("%H:%M:%S")
    except Exception:
        timestamp = ""
    bpm = item.get("value", {}).get("bpm", "")
    # Filter by start/end time
    if timestamp:
        t = datetime.strptime(timestamp, "%H:%M:%S")
        if start_time <= t <= end_time:
            # Subtract start_time from t
            delta = (t - start_time)
            # If negative, skip (shouldn't happen due to filter)
            if delta.total_seconds() >= 0:
                # Format as hh:mm:ss
                seconds = int(delta.total_seconds())
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                secs = seconds % 60
                diff_str = f"{hours:02}:{minutes:02}:{secs:02}"
                rows.append({"timestamp": diff_str, "bpm": bpm})


# Write to TSV
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp", "bpm"], delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)

print(f"Filtered TSV written to: {OUTPUT_FILE}")
