# Predictive Maintenance Service

## Overview

This subcomponent, part of the Predictive Maintenance component, focuses on the Analysis of SEW data (CORIM file-Machine failure history, in which info related to MTBF, duration maintenance interventions, type of maintenance activity, downtime, etc.)
 
 ## Table of Contents
 1. [Dataset](#dataset)
 2. [Files Description](#files-description)
 3. [Installation](#installation)
 4. [Usage](#usage)
 5. [Contributor](#contributor)

 ## Dataset



 ## Files Description

The input of genetic algorithm includes 2 files: data.xlsx and activity.xlsx

1. data.xlsx: Contains the parameters of the components within the production line (Alpha, Beta, Average maintenance duration).

2. activity.xlsx: Includes the parameter (Replacement time) related to maintenance activities in the production line, with each activity mapped to its corresponding component (each row of activity has the corresponding Component ID).

3. Defined constants in main.py and check_fitness.py
    - C_s: setup cost
    - C_d: downtime cost rate
    - m: number of repairmen


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

1. Start the application:
```bash
python GUI.py
```
2. Enter input values:
    - C_s: is the setup cost which is the same for all components which can be shared if several components are maintained together.
    - C_d: is a positive constant representing downtime cost rate related to production loss.
    - m: is the number of repairmen available in the production line.
3. User interface displays:
    - Cost saving when doing group maintenance for components in production line.
    - Time and duration to do maintenance in each component.
    - Visual graph on time domain.

## Contributor

Huu-Truong Le, Université de Lorraine