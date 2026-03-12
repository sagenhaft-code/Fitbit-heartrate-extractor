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
                # Round to nearest 5 seconds
                seconds = int(delta.total_seconds())
                seconds = ((seconds + 2) // 5) * 5
                # Format as hh:mm:ss
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                secs = seconds % 60
                diff_str = f"{hours:02}:{minutes:02}:{secs:02}"
                rows.append({"timestamp": diff_str, "bpm": bpm})


# Merge duplicates by averaging BPM
from collections import OrderedDict
merged = OrderedDict()
for row in rows:
    ts = row["timestamp"]
    if ts in merged:
        merged[ts].append(int(row["bpm"]))
    else:
        merged[ts] = [int(row["bpm"])]
duplicate_count = sum(len(bpms) - 1 for bpms in merged.values())
print(f"Duplicates found: {duplicate_count}")
rows = [{"timestamp": ts, "bpm": round(sum(bpms) / len(bpms))} for ts, bpms in merged.items()]


# Check for missing 5-second intervals
total_range_seconds = int((end_time - start_time).total_seconds())
expected_count = total_range_seconds // 5 + 1
actual_timestamps = set(row["timestamp"] for row in rows)
actual_count = len(actual_timestamps)
missing_count = expected_count - actual_count
missing_pct = (missing_count / expected_count) * 100 if expected_count > 0 else 0

biggest_gap = 0
biggest_gap_start = ""
biggest_gap_end = ""
sorted_seconds = sorted(
int(ts.split(":")[0]) * 3600 + int(ts.split(":")[1]) * 60 + int(ts.split(":")[2])
for ts in actual_timestamps
)
for i in range(1, len(sorted_seconds)):
    gap = sorted_seconds[i] - sorted_seconds[i - 1]
    if gap > biggest_gap:
        biggest_gap = gap
        s = sorted_seconds[i - 1]
        e = sorted_seconds[i]
        biggest_gap_start = f"{s // 3600:02}:{(s % 3600) // 60:02}:{s % 60:02}"
        biggest_gap_end = f"{e // 3600:02}:{(e % 3600) // 60:02}:{e % 60:02}"

print(f"Missing datapoints: {missing_count}/{expected_count} ({missing_pct:.1f}%)")
if biggest_gap > 0:
    print(f"Biggest gap: {biggest_gap}s (from {biggest_gap_start} to {biggest_gap_end})")


# Write to TSV
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp", "bpm"], delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)

print(f"Filtered TSV written to: {OUTPUT_FILE}")
