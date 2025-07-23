# Predictive Maintenance Service - Threshold based maintenance

## Service description

PdM2 service is designed to monitor the health status of different SEW production modules, where the evolution of the frequency of historical failures is used as the health indicator. Such monitoring is carried out automatically (performed by an external MODAPTO component) with a frequency that is specific to each module, and it results in inspection or replacement suggestions for the most critical sub elements that compose a certain module (for more contextual details please refer to Deliverable 5.2).

The service is structured as a python class called PdM2, which can be invoked. See below:

```sh
PdM2Service( input_data, winds_count_component_replac=3, output_path="maintenance_recommendations.json")
```

The PdM2Service arguments necessary to instantiate the class are detailed below.

## Inputs

“Input data” requires a JSON object that should contain historical failure data and parameters for module monitoring. An example of a JSON object is provided below while a description of its content is provided hereafter. 

```sh
{
    "events": [
        {
            "Stage": "MU MOTG",
            "Cell": "LIGNE DE MONTAGE MOTG04",
            "Module ID": 100019,
            "Component ID": 100020,
            "Failure Type (electrical/mechanical)": "Mechanic",
            "Failure description": "ascenseur ne monte pas retournement",
            "Maintenance Action performed": "Réglage capteur sorti indexeur\n----- Mickael KLEIN 16/06/2023 08:01 -----",
            "Component replacement (yes/no)": "no",
            "Name": "Carlos M",
            "TS Intervention started": "16/06/2023 06:38:18"
        },
        {
            "Stage": " MU MOTG ",
            "Cell": "LIGNE DE MONTAGE MOTG04",
            "Module ID": 100019,
            "Component ID": 100025,
            "Failure Type (electrical/mechanical)": "Mechanic",
            "Failure description": "Donner suite à la panne sur les rippeurs. Remise en état !",
            "Maintenance Action performed": "Intervention réalisée le 22 novembre 2023\r\n----- Damien Kuhn 23/11/2023 08:34 -----",
            "Component replacement (yes/no)": "no",
            "Name": "Carlos M",
            "TS Intervention started": "08/11/2023 10:13:56"
        }
    ],
    "parameters":{
        "module_ID": 100019,
        "components_ID": [100020, 100021, 100022, 100023, 100024],
        "window_size": 90,
        "inspection_threshold": 3,
        "replacement_threshold": 7
    }
}

```
Description of the content of the JSON object

**Events:** up-to-date failure records (drift table). It contains details about failure and maintenance events such as: “Stage”, “Cell”, “Module ID”, “Component ID”; “Failure Type”, “Failure description”, “Maintenance Action performed”, “Component replacement (yes/no)”, “Name”, “TS Intervention started”.

**Parameters:** parameters for monitoring a module. It contains: the “module ID”, which defines the module to be monitored; “components ID”, which defines an array of components that constitute the module and for which maintenance suggestions are desired; the “window_size”, which defines the amount of data (failure period in days) used to measure the health of the module; “inspection_threshold”, which is the number of failures that triggers an inspection; “replacement_threshold”, which is the number of failures that triggers a replacement. Note that all these parameters are fixed but they are module-specific, as so, the API should enable the user to configure these values for each production module within the MODAPTO environment and add new production modules to be monitored with the respective parameters if necessary. Such values are defined based on expert-knowledge or exploratory analysis of failure data and they do not change dynamically. 

While the JSON input was provided beforehand,  an input sample is also provided as .json file in the sharepoint repository under the name “CORIM_tool_test.json”. 

The second PdM2Service argument called “winds_count_component_replac” is the number of time windows to measure the health state of the sub elements and used to define the most critical sub element to be replaced. It has a fixed value and is independent of the module or component. Consequently, it does not need to be provided when invoking the class, i.e., the default value is enough. 

The third PdM2Service argument “output_path="maintenance_recommendations.json" corresponds to the path where the maintenance suggestions will be stored, with “maintenance_recommendations.json” as the default path/file name. 

## Output

The output of the algorithm is a .json file with default name “maintenance_recommendations.json”. The file follows the following format when no recommendation is given. 

```sh
{
  "recommendation": "non",
  "details": "The system is under control"
}
```
The file follows the following format when a recommendation is given. 
```sh
{
  "recommendation": "schedule a replacement of sub element 100019",
  "details": "It failed 16 times in the last 270 days"
}
```
- "recommendation" corresponds to the maintenance actions to be scheduled in the next available maintenance slot.
- "details" corresponds to contextual information that justify the maintenance recommendation.

Note that the last output scenario (when a recommendation is given) should be converted to notifications, which can be used to schedule maintenance actions and to update production schedules accordingly. As agreed between UL and ATC: “These notifications should be incorporated as part of the input for Optimization Service. It can be done manually by creating assignments from the PdM2 notifications to re-schedule and add the details of the notification to the Opt.Service input”.

## Requirements for API
The service should contain a configuration button/area that configure PdM2 monitoring for different production modules and potential new modules. The user (potentially in charge of maintaining the code/service) can input a set of modules of interest to be monitored and its specific monitoring frequencies. This input will also contain “window_size”, “components ID”, “inspection_threshold”, and “replacement_threshold”. 

An external scheduler triggers the service automatically given the configuration of PdM2, i.e., the set of modules to be monitored and the respective frequency of each module. The scheduler then passes an input to the PdM2 algorithm as JSON object, containing the information defined in the JSON example provided in section 2 and tailored to the specific production module to be monitored, i.e., the most up-to-date failure data (historical drift table) and the parameters for monitoring the module.

Given that the logic for generalization (different production modules) was already stablished, the initial set of modules to be monitored for this version could contain just the module press (100019) with the following parameter values:

```sh
{
  "100019": {
    "monitoring_frequency": 5,
    "components_ID": [100020, 100021, 100022, 100023, 100024],
    "window_size": 90,
    "inspection_threshold": 3,
    "replacement_threshold": 7
  }
}
```
This set can be extended by the user if a new module is added to SEW production or if other modules are considered for monitoring. For the moment more modules are not added since the monitoring parameters have been only  validated for the press. 

**Invoking PdM2**

An example for invoking PdM2 is provided below using the JSON example provided in section 2.
```sh
# Example of usage:
from pdm2_service import PdM2Service
# This is where your API receives input_data (e.g., via POST request)
input_data = {
    "events": [...],
    "parameters": {...}
}

service = PdM2Service(input_data=input_data)
output = service.run()
```