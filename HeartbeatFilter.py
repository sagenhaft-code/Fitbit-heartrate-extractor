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


# Ensure 00:00:00 exists, copy BPM from the first available entry if not
if not any(row["timestamp"] == "00:00:00" for row in rows):
    first_bpm = rows[0]["bpm"] if rows else ""
    rows.insert(0, {"timestamp": "00:00:00", "bpm": first_bpm})

# Fill in missing 5-second intervals with empty BPM
existing = {row["timestamp"] for row in rows}
lookup = {row["timestamp"]: row for row in rows}
filled_rows = []
for i in range(0, total_range_seconds + 1, 5):
    h = i // 3600
    m = (i % 3600) // 60
    s = i % 60
    ts = f"{h:02}:{m:02}:{s:02}"
    if ts in lookup:
        filled_rows.append(lookup[ts])
    else:
        filled_rows.append({"timestamp": ts, "bpm": ""})
rows = filled_rows


# Ask whether to also output the file with missing intervals filled in
fill_missing = input("Also output file with missing intervals (empty BPM) to fill? (y/n): ").strip().lower()
if fill_missing == "y":
    tofill_filename = Path(input_filename).stem + "_tofill.tsv"
    tofill_path = DATA_DIR / tofill_filename
    with open(tofill_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "bpm"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"To-fill TSV written to: {tofill_path}")


# Linear approximation for missing timestamps
i = 0
while i < len(rows):
    if rows[i]["bpm"] == "":
        # Find start of gap (last non-empty before this)
        start_idx = i - 1
        # Find end of gap (next non-empty after this)
        end_idx = i
        while end_idx < len(rows) and rows[end_idx]["bpm"] == "":
            end_idx += 1
        # Number of missing + 1
        gap_count = end_idx - start_idx  # includes both endpoints distance
        if start_idx >= 0 and end_idx < len(rows):
            bpm_start = float(rows[start_idx]["bpm"])
            bpm_end = float(rows[end_idx]["bpm"])
            step = (bpm_end - bpm_start) / gap_count
            for j in range(start_idx + 1, end_idx):
                pos = j - start_idx
                rows[j]["bpm"] = round(bpm_start + step * pos, 1)
        elif start_idx >= 0:
            for j in range(start_idx + 1, end_idx):
                rows[j]["bpm"] = float(rows[start_idx]["bpm"])
        elif end_idx < len(rows):
            for j in range(i, end_idx):
                rows[j]["bpm"] = float(rows[end_idx]["bpm"])
        i = end_idx
    else:
        i += 1


# Round all BPM values to integers
import math
for row in rows:
    if row["bpm"] != "":
        val = float(row["bpm"])
        row["bpm"] = math.floor(val + 0.5)


# Write to TSV
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp", "bpm"], delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)

print(f"Filtered TSV written to: {OUTPUT_FILE}")
