import pandas as pd
from datetime import datetime, timedelta
import json

# Parameters
module_ID = 100019
components_ID = [100020, 100021, 100022, 100023,100024]
window_size = 90
inspection_threshold = 3
replacement_threshold = 7
winds_count_component_replac = 3

# Load JSON
with open('CORIM_tool_test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.json_normalize(data)

# Convert timestamp column to datetime
df['event date'] = pd.to_datetime(df['event date'], dayfirst=True)

# Define time windows
today = pd.Timestamp.today().normalize()
#today = pd.to_datetime("21/08/2024", dayfirst=True)
window_size_days_ago = today - pd.Timedelta(days=window_size)
extraction_days_ago = today - pd.Timedelta(days=winds_count_component_replac * window_size)

# Filter recent events (inspection)
recent_failures_window_size = df[
    (df['module'] == module_ID) &
    (df['event date'] >= window_size_days_ago) &
    (df['event date'] <= today)]

# Filter recent events (replacement)
recent_failures_extraction = df[
    (df['module'] == module_ID) &
    (df['event date'] >= extraction_days_ago) &
    (df['event date'] <= today)]

# Maintenance decision logic
module_count = len(recent_failures_window_size)

if inspection_threshold <= module_count < replacement_threshold:
    components_count = recent_failures_window_size['component'].value_counts()
    most_failed_component = components_count.idxmax()
    max_failures = components_count.max()
    print(f"Please schedule an inspection of sub element {most_failed_component}.\nIt failed {max_failures} times in the last {window_size} days.")

elif replacement_threshold <= module_count:
    components_count = recent_failures_extraction['component'].value_counts()
    most_failed_component = components_count.idxmax()
    max_failures = components_count.max()
    print(f"Please schedule a replacement of sub element {most_failed_component}.\nIt failed {max_failures} times in the last {window_size * winds_count_component_replac} days.")

else:
    print("The system is under control.")
