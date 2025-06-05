"""
The algorithm takes the latest information of failures to update a health indicator and send notifications of inspections or repleacement actions when such health
indicator is not adequate. The dataset is updated by the maintenance operator as the times goes by. It informs details about the failure of module/sub elements and the minimal
repairs performed.

In this version:
-monitoring is performed periodically and lunched by the user manually in the current implementation.
-the user does no need to input the SEW module ID. It is defined by default as the press. In future versions the user can define the module ID and the algorithm would contain
a dictionary of the hierarchical structure of SEW components
"""
import pandas as pd
from datetime import date
import pandas as pd
from datetime import datetime, timedelta

#input module ID and sub components ID: in the future the user can input the module ID, and the tool will search the corresponding IDs (list of module+subelements IDs) within a dictionary
#that contains the hierarchical structure of the different modules in each line.

#Parameters
module_ID = 100019
components_ID = [100020, 100021, 100022, 100023,100024]
window_size = 90
inspection_threshold = 3
replacement_threshold = 7 #change this parameter to simulate inspections or replacements
winds_count_component_replac= 3

df = pd.read_csv('CORIM_tool_test.csv', delimiter=';', encoding='ISO-8859-1')
#print(type(df['event date'].iloc[0]))
# Convert timestamp column to datetime if needed
df['event date'] = pd.to_datetime(df['event date'], dayfirst=True)

#retrieve data for IDs that are reported within the last n time windows (for this example each window correspond to 30 days, we retrieve 90 days of data) based on today data.
extraction = winds_count_component_replac*window_size
# Get today's date and date 'extraction' days ago
today = pd.Timestamp.today().normalize()
#today = pd.to_datetime("21/08/2024", dayfirst=True)
window_size_days_ago = today - pd.Timedelta(days=window_size)
extraction_days_ago = today - pd.Timedelta(days=extraction)

# Filter data: selected components AND within latest days (respective horizons to estimate the health for inspection or replacement suggetsions)
#for inspection suggestions
recent_failures_window_size = df[
    (df['module'] == module_ID) &
    (df['event date'] >= window_size_days_ago) &
    (df['event date'] <= today)]
#for replacement suggestions
recent_failures_extraction = df[
    (df['module'] == module_ID) &
    (df['event date'] >= extraction_days_ago) &
    (df['event date'] <= today)]

#count the total number of events at module level for the last window_size days
module_count = len(recent_failures_window_size)
#print(module_count)
if inspection_threshold <= module_count < replacement_threshold:
    #count the number of failures per ID during the last window_size days
    components_count = recent_failures_window_size['component'].value_counts()
    most_failed_component = components_count.idxmax()
    max_failures = components_count.max()
    print(f"Please schedule an inspection of sub element {most_failed_component} for the next maintenance slot available.\n")
    print(f"Details of the call: Sub element {most_failed_component} had the highest failure count with {max_failures} failures in the last {window_size} days.")

elif replacement_threshold<= module_count:
    #count the number of failures per ID during the last winds_count_component_replac*window_size days
    components_count = recent_failures_extraction['component'].value_counts()
    most_failed_component = components_count.idxmax()
    max_failures = components_count.max()
    print(f"Please schedule a replacement of the critical component of sub element {most_failed_component} for the next maintenance slot available.\n")
    print(f"Details of the call:\nSub element {most_failed_component} had the highest failure count with {max_failures} failures in the last {extraction} days.")

else:
    print ("The system is under control")