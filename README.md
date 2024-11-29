# Predictive-Maintenance

## Overview

This subcomponent, part of the Predictive Maintenancce component, focuses on the Analysis of SEW data (CORIM file-Machine failure history, in which info related to MTBF, duration maintenance interventions, type of maintenance activity, downtime, etc.)
 
 ## Table of Contents
 1. [Installation](#installation)
 2. [Usage](#usage)
 3. [Contributor](#contributor)

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

1. To run the Genetic Algorithm to find the optimal maintenance actions, run main.py:
```bash    
python main.py
```
2. To check the cost-saving/fitness of the Genetic Algorithm given the maintenance actions, run check_fitness.py:
```bash    
python check_fitness.py
```
## Contributor

Huu-Truong Le, Université de Lorraine