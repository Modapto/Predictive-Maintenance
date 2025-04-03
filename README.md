# Predictive Maintenance Service

## Overview

This is a desktop application that ipmlements Predictive Maintenance Service. The purpose of the service is to provide an optimal scheduling of the maintenance action to be performed on a line or system. The output of the service will be for a list of maintenance actions and time to be performed for each component/group of components.
 
## Table of Contents
1. [Dataset](#dataset)
2. [Project Structure](#project-structure)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Input/Output description](#inout_description)
6. [Service description](#service_description)
7. [Contributor](#contributor)

## Dataset
The dataset are manually extracted from CORIM.xlsx file provided by SEW USOCOME, then divided into 2 files: 
1. component.json: Contains the parameters of the components within the production line (Alpha, Beta, Average maintenance duration).
2. activity.json: Includes the parameter (Replacement time) related to maintenance activities in the production line, with each activity mapped to its corresponding component (each row of activity has the corresponding Component ID).

## Project Structure
```
Predictive-Maintenance/
├── dataset/                       
│   ├── activity.json              # Including data related to the failures of the components in the time window
│   ├── component.json             # Including data related to specification of the components in the production line
├── algorithm/                 
│   ├── algorithm.py               # Genetic algorithm imlementation
├── input/ 
│   ├── input.py                   # User input from keyboard
├── output/                    
│   ├── result.json                # Output of predictive maintenance service within the defined time window
├── debug/                     
│   ├── check_fitness.py           # Debugging file
```

## Installation

1. Clone the repository: 
```bash    
git clone https://github.com/Modapto/Predictive-Maintenance.git
cd Predictive-Maintenance
```
2. Create, activate a virtual environment, and install the packages from the requirements.txt file:
```bash    
python -m venv virtual_env
source virtual_env/Scripts/activate
pip install -r requirements.txt
```

## Usage
Run the program
```bash
cd algorithm
python algorithm.py
```
## Input/Output description
1. input.py
    - setup_cost: is the setup cost which is the same for all components which can be shared if several components are maintained together. (datatype: float)
    - downtime_cost_rate: is a positive constant representing downtime cost rate related to production loss. (datatype: float)
    - no_repairmen: is the number of repairmen available in the production line. (datatype: interger)

2. output.json: is a json file containing
    - "Cost savings": cost saving for grouping maintenance plan.
    - "Grouping maintenance": grouping maintenance plan.
    - "Individual plan": individual maintenance plan.
    - "Time window": maintenance time window.
```
{
    "Cost savings": 101.42000000000007,                                 # float
    "Grouping maintenance": {
        "Group 1": [
            {
                "Component ID": 0,                                      # integer
                "Component name": "POSTE DE CONTRÔLE",                  # string
                "Replacement time": 349.571,                            # float
                "Duration": 4.957                                       # float
            },
            {
                "Component ID": 1,                                      # integer       
                "Component name": "CONNECTEURS",                        # string
                "Replacement time": 349.571,                            # float
                "Duration": 4.957                                       # float
            }
        ],
        ...
    },
    "Individual maintenance": {
        "Group 1": [
            {  
            "Component ID": 0,                                          # integer        
                "Component name": "POSTE DE CONTRÔLE",                  # string
                "Replacement time": 173.298,                            # float
                "Duration": 1.108                                       # float
            }
        ],
        ...
    },
    "Time window": {
        "Begin": 0.0,                                                   # float
        "End": 1000.0                                                   # float
    }
}
```
## Service description
1. sffsfsf

## Contributor

Huu-Truong Le, Université de Lorraine