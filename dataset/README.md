# Predictive Maintenance Service - Grouping maintenance

## Service description

This service provides predictive maintenance scheduling capabilities within the MODAPTO ecosystem. The purpose of the service is to provide an optimal scheduling of the maintenance action to be performed on a line or system. The output of the service will be for a list of maintenance actions and time to be performed for each component/group of components.

## JSON file input (Component Configuration File)

The "component.json" file: Contains the parameters of the components within the production line (Equipment ID, Component name, Alpha, Beta, Average maintenance duration, Mean time between failure, Last Maintenance Action Time). 

**Description:**
- "Component": denotes the unique ID number for an equipment in the production line, as defined in CORIM.
- "Module": denotes the name of the equipment.
- "Alpha" and "Beta": Penalty cost function parameters used in the genetic algorithm; defined by maintenance engineering.
- "Average maintenance duration": The average time (in hours) to fix the equipment if it fails.
- "MTBF":Mean time between failure of the component.
- "Last Maintenance Action Time": this information comes from the CORIM file by requesting the last maintenance action time for the ID component.

***Note:***
- There are some values in "MTBF" and "Last Maintenance Action Time" missing, this will be filled after discussing with SEW about this dataset format later.

```sh
[
    {
        "Component": 100054,
        "Module": "POSTE DE CONTRÔLE",
        "Alpha": 5,
        "Beta": 16.0,
        "Average maintenance duration": 1.108,
        "MTBF": 173.298,
        "Last Maintenance Action Time": ...
    },
    {
        "Component": 105678,
        "Module": "CONNECTEURS",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 3.849,
        "MTBF": 179.545,
        "Last Maintenance Action Time": ...
    },
    {
        "Component": 100045,
        "Module": "POSTE 09 : MONTAGE CÔTÉ A (RETOURNEMENTS)",
        "Alpha": 5,
        "Beta": 20.0,
        "Average maintenance duration": 0.726,
        "MTBF": 208.829,
        "Last Maintenance Action Time": ...
    },
    {
        "Component": 100019,
        "Module": "POSTE 04  : EMMANCHEMENTS ROULEMENTS (PRESSE)",
        "Alpha": 5,
        "Beta": 20.0,
        "Average maintenance duration": 1.925,
        "MTBF": 548.357,
        "Last Maintenance Action Time": ...
    },
    {
        "Component": 100006,
        "Module": "CONVOYEURS",
        "Alpha": 5,
        "Beta": 10.0,
        "Average maintenance duration": 0.492,
        "MTBF": 627.938,
        "Last Maintenance Action Time": ...
    },

    ...

]
```

## User input 

The "input.py" file contains global parameters for the maintenance scheduling service and is set by the user, including:
- setup_cost: (float) is the setup cost which is the same for all components which can be shared if several components are maintained together.
- downtime_cost_rate: (float) is a positive constant representing downtime cost rate related to production loss.
- no_repairmen: (interger) is the number of repairmen available in the production line.


## Service output

The service generates an output JSON file (output.json) containing the optimized maintenance scheduling results. The output provides decision support for maintenance planning, considering both individual and grouped maintenance strategies.

The output.json is a json file containing:
- "Cost savings": cost saving for grouping maintenance plan.
- "Grouping maintenance": grouping maintenance plan.
- "Individual plan": individual maintenance plan.
- "Time window": maintenance time window.

```sh
{
    "Cost savings": 101.42000000000007,  // float
    "Grouping maintenance": {
        "Group 1": [
            {
                "Component": 100054,                                      // integer
                "Equipment name": "POSTE DE CONTRÔLE",                  // string
                "Replacement time": 349.571,                           // float
                "Duration": 4.957                                       // float
            },
            {
                "Component": 1,                                      // integer
                "Equipment name": "CONNECTEURS",                        // string
                "Replacement time": 349.571,                            // float
                "Duration": 4.957                                       // float
            }
        ],
        ...
    },
    "Individual maintenance": {
        "Group 1": [
            {  
                "Component": 100054,                                      // integer
                "Equipment name": "POSTE DE CONTRÔLE",                  // string
                "Replacement time": 173.298,                            // float
                "Duration": 1.108                                       // float
            }
        ],
        ...
    },
    "Time window": {
        "Begin": 0.0,                                                   // float
        "End": 1000.0                                                   // float
    }
}
```