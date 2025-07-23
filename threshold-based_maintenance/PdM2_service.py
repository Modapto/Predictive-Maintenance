import pandas as pd
from datetime import datetime, timedelta
import json
import ast


class PdM2Service:
    def __init__(self, input_data, winds_count_component_replac=3,
                 output_path="maintenance_recommendations.json"):

        self.failure_data = pd.DataFrame(input_data['events'])
        self.module_ID = input_data['parameters']['module_ID']
        self.window_size = int(input_data['parameters']['window_size'])
        self.inspection_threshold = int(input_data['parameters']['inspection_threshold'])
        self.replacement_threshold = int(input_data['parameters']['replacement_threshold'])
        self.winds_count_component_replac = winds_count_component_replac
        #self.components_ID = ast.literal_eval(input_data['parameters']['components_ID'])
        self.components_ID = input_data['parameters']['components_ID']
        self.output_path = output_path

        self.df = self._load_data()
        self.result = {}

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

        failures_extraction = self.df[
            (self.df['Module ID'] == self.module_ID) &
            (self.df['TS Intervention started'] >= ext_days_ago) &
            (self.df['TS Intervention started'] <= today)
            ]

        return failures_window_size, failures_extraction

    def _make_decision(self):
        failures_window_size, failures_extraction = self._filter_failures()
        module_count = len(failures_window_size)

        if self.inspection_threshold <= module_count < self.replacement_threshold:
            return self._create_result(failures_window_size, "inspection", self.window_size)

        elif module_count >= self.replacement_threshold:
            return self._create_result(failures_extraction, "replacement",
                                       self.window_size * self.winds_count_component_replac)

        else:
            return {
                "recommendation": "non",
                "details": "The system is under control"
            }

    def _create_result(self, failure_data, action, period):
        filtered_data = failure_data[failure_data['Component ID'].isin(self.components_ID)]
        components_count = filtered_data['Component ID'].value_counts()
        
        if not components_count.empty:
            most_failed = components_count.idxmax()
            max_count = components_count.max()
        else:
            most_failed = None
            max_count = 0

        recommendation = f"schedule an {action} of sub element {most_failed}"
        details = f"it failed {max_count} time(s) in the last {period} days."

        return {
            "recommendation": recommendation,
            "details": details
        }

    def run(self):
        self.result = self._make_decision()
        self._save_output()
        return self.result

    def _save_output(self):
        with open(self.output_path, "w", encoding="utf-8") as file:
            json.dump(self.result, file, indent=2)


