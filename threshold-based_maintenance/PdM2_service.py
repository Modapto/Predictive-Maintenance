import pandas as pd
from datetime import datetime, timedelta
import json
import ast


class PdM2Service:
    def __init__(self, input_data,
                 output_path="maintenance_recommendations.json"):

        self.failure_data = pd.DataFrame(input_data['events'])
        self.module_ID = str(input_data['parameters']['module_ID'])
        self.window_size = int(input_data['parameters']['window_size'])
        self.inspection_threshold = int(input_data['parameters']['inspection_threshold'])
        self.replacement_threshold = int(input_data['parameters']['replacement_threshold'])
        self.winds_count_component_replac = 3
        #self.components_ID = ast.literal_eval(input_data['parameters']['components_ID'])

        # Convert components_ID elements to strings
        self.components_ID = [str(x) for x in input_data['parameters']['components_ID']]
        self.output_path = output_path
        self.durations = [0, 1, 2]  # Changed "non" to 0 to ensure Duration is always an integer

        self.df = self._load_data()
        self.result = {}
        
        for i in input_data['events']:
            if i["Module ID"] == self.module_ID:
                self.Cell = i["Cell"]
                break        


    def _load_data(self):
        df = self.failure_data
        df['TS Intervention started'] = pd.to_datetime(df['TS Intervention started'],  format='mixed', errors='coerce')
        return df

    def _filter_failures(self):
        today = pd.Timestamp.today().normalize()
        #today = pd.to_datetime("21/06/2023", dayfirst=True)
        ws_days_ago = today - pd.Timedelta(days=self.window_size)
        ext_days_ago = today - pd.Timedelta(days=self.winds_count_component_replac * self.window_size)

        failures_window_size = self.df[
            (self.df['Module ID'] == self.module_ID) &
            (self.df['TS Intervention started'] >= ws_days_ago) &
            (self.df['TS Intervention started'] <= today)
            ]
        print(f'module_ID in params is {self.module_ID} of type {type(self.module_ID)}')
        print(f'components_ID in params is {self.components_ID} of type {type(self.components_ID[0])}')
        print(f'values of module ID in events are {type(self.df["Module ID"][0])}')
        print(f'values of component ID in events are {type(self.df["Component ID"][0])}')
        print(f'initial date of window is {ws_days_ago}of type {type(ws_days_ago)}')
        print(f'final date of window is {today} of type {type(today)}')
        print(f'window size is {self.window_size}')
        print(f'the date type in events is {type(self.df["TS Intervention started"][0])}, for example {self.df["TS Intervention started"][0]}')

        failures_extraction = self.df[
            (self.df['Module ID'] == self.module_ID) &
            (self.df['TS Intervention started'] >= ext_days_ago) &
            (self.df['TS Intervention started'] <= today)
            ]
        return failures_window_size, failures_extraction

    def _make_decision(self):
        failures_window_size, failures_extraction = self._filter_failures()
        module_count = len(failures_window_size)
        print(f'the number of failures in the module is {module_count}')
        print(f'inspection threshold is {self.inspection_threshold}, replacement threshold is {self.replacement_threshold}')

        if self.inspection_threshold <= module_count < self.replacement_threshold:
            duration = self.durations[1]
            return self._create_result(failures_window_size, "inspection", self.window_size, duration)

        elif module_count >= self.replacement_threshold:
            duration = self.durations[2]
            return self._create_result(failures_extraction, "replacement",
                                       self.window_size * self.winds_count_component_replac, duration)
        else:
            duration = self.durations[0]
            return self._create_result(failures_window_size, "non", self.window_size, duration)

            """
            return {
                "recommendation": "non",
                "details": "The system is under control"
            }
            """

    def _create_result(self, failure_data, action, period, duration):
        filtered_data = failure_data[failure_data['Component ID'].isin(self.components_ID)]
        components_count = filtered_data['Component ID'].value_counts()
        
        if not components_count.empty:
            most_failed = components_count.idxmax()
            max_count = components_count.max()
        else:
            most_failed = "None"  # Changed from None to string value
            max_count = 0

        print(f'MOST_FAILED:{most_failed}')
        print('TTTTTEST222222')

        #recommendation = f"schedule an {action} of sub element {most_failed}"
        if duration == 0:  # Changed from "non" to 0 since duration is always an integer
            details = f"The system is under control"
        else:
            details = f"{max_count} failure(s) in the last {period} days."

        return {
            "Recommendation": action,
            "Duration": duration,
            "Sub element ID": most_failed,
            "Module ID": self.module_ID,
            "Cell": self.Cell,
            "Details": details,
        }

    def run(self):
        self.result = self._make_decision()
        self._save_output()
        return self.result

    def _save_output(self):
        with open(self.output_path, "w", encoding="utf-8") as file:
            json.dump(self.result, file, indent=2)


