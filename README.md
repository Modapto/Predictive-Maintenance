# Predictive-Maintenance

## Overview

This subcomponent, part of the Predictive Maintenancce component, focuses on the Analysis of SEW data (CORIM file-Machine failure history, in which info related to MTBF, duration maintenance interventions, type of maintenance activity, downtime, etc.)
 
 ## Table of Contents
 1. [Input] (#input)
 2. [Installation](#installation)
 3. [Usage](#usage)
 4. [Contributor](#contributor)

 ## Input description
The input of genetic algorithm includes 2 files: data.xlsx and activity.xlsx

1. data.xlsx: Contains the parameters of the components within the production line (Alpha, Beta, Average maintenance duration).

2. activity.xlsx: Includes the parameter (Replacement time) related to maintenance activities in the production line, with each activity mapped to its corresponding component (each row of activity has the corresponding Component ID).


 ## Installation

1. Create, activate a virtual environment, and install the packages in the requirements.txt file:
```bash    
python -m venv virtual_env
source virtual_env/bin/activate
pip install -r requirements.txt
```

 2. Clone the repository: 
```bash    
git clone https://github.com/Modapto/Predictive-Maintenance.git
cd Predictive-Maintenance
```

## Usage

1. To run the Genetic Algorithm to find the optimal maintenance actions, run main.py, this will find the set of optimal activities should be grouped:
```bash    
python main.py
```
2. To check the cost-saving/fitness of the Genetic Algorithm given the maintenance actions, run check_fitness.py, this will output the cost saving based on the set of optimal activities:
```bash    
python check_fitness.py
```
## Contributor

Huu-Truong Le, Université de Lorraine