# Predictive Maintenance Service

## Overview

This is a desktop application that imlements Predictive Maintenance Service. The purpose of the service is to provide an optimal scheduling of the maintenance action to be performed on a line or system. The output of the service will be for a list of maintenance actions and time to be performed for each component/group of components.

It additionally provides an API to retrieve all important information (Input Data, Algorithm parameters and User Input) and execute the genetic algorithm.

## Table of Contents

1. [Dataset](#dataset)
2. [Project Structure](#project-structure)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Input/Output description](#inputoutput-description)
6. [Function description](#function-description)
7. [Deployment](#deployment)
8. [API](#api)
9. [Contributors](#contributors)

## Dataset

The dataset are manually extracted from CORIM.xlsx file provided by SEW USOCOME, then divided into 2 files:
1.component.json: Contains the parameters of the components within the production line (Alpha, Beta, Average maintenance duration).
2.activity.json: Includes the parameter (Replacement time) related to maintenance activities in the production line, with each activity mapped to its corresponding component (each row of activity has the corresponding Component ID).

## Project Structure

```sh
Predictive-Maintenance/
├── dataset/                       
│   ├── activity.json              # Including data related to the failures of the components in the time window
│   ├── component.json             # Including data related to specification of the components in the production line
├── algorithm/                 
│   ├── algorithm.py               # Genetic algorithm imlementation
│   ├── parameters.py              # Parameters of genetic algorithm
├── input/ 
│   ├── input.py                   # User input from keyboard
├── output/                    
│   ├── result.json                # Output of predictive maintenance service within the defined time window
├── debug/                     
│   ├── check_fitness.py           # Debugging file
main.py                            # FastAPI endpoints
Dockerfile                         # For Containerization
```

## Installation

1.Clone the repository:

```bash
git clone https://github.com/Modapto/Predictive-Maintenance.git
cd Predictive-Maintenance
```

2.Create, activate a virtual environment, and install the packages from the requirements.txt file:

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
    - setup_cost: (float) is the setup cost which is the same for all components which can be shared if several components are maintained together.
    - downtime_cost_rate: (float) is a positive constant representing downtime cost rate related to production loss.
    - no_repairmen: (interger) is the number of repairmen available in the production line.

2. output.json: is a json file containing
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
                "Component ID": 0,                                      // integer
                "Component name": "POSTE DE CONTRÔLE",                  // string
                "Replacement time": 349.571,                           // float
                "Duration": 4.957                                       // float
            },
            {
                "Component ID": 1,                                      // integer
                "Component name": "CONNECTEURS",                        // string
                "Replacement time": 349.571,                            // float
                "Duration": 4.957                                       // float
            }
        ],
        ...
    },
    "Individual maintenance": {
        "Group 1": [
            {  
            "Component ID": 0,                                          // integer
                "Component name": "POSTE DE CONTRÔLE",                  // string
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

## Function description

1. To initiate the algorithmic process, call the genetic_algorithm() method:
    - Input:
        - genome_length, population_size, generations, p_c_min, p_c_max, p_m_min, p_m_max: parameters of genetic algorithm (see parameters.py).
        - m, C_s, C_d: user input from keyboard (see [Input/Output description](#inputoutput-description)), corresponding to Number of repairmen, Setup cost, Downtime cost rate respectively.

    - Output:
        - best_individual: (list) contain the optimal encoding of the maintenance plan
        - best_fitness: (float) cost saving of the maintenance plan

    ```python
    def genetic_algorithm(genome_length: integer, m: integer, population_size: integer, generations: integer, p_c_min: float, p_c_max: float, p_m_min: float, p_m_max: float, C_s: float, C_d: float):
        ...
        return best_individual, best_fitness
    ```

2.To export the result of maintenance plan, call the output_json_file() method:

The result is saved in result.json

```python
    def output_json_file(best_individual: list, best_fitness: float, t_begin: float, t_end: float):
        ...
```

## Deployment

The application can also serve as a Web Service deployed as container. To run the container follow the below instructions:

1. Ensure Docker or equivalent application is installed and running.

2. Build the Docker container:

    ```sh
    docker build -t modapto-predictive-maintenace .
    ```

3. Run the Docker container including the environmental variables:

    ```sh
    docker run -d -p 8000:8000 \
    --name modapto-predictive-maintenace \
    -e SWAGGER_SERVER_URL="http://localhost:8000" \
    modapto-predictive-maintenace
    ```

4. To stop container run:

    ```sh
   docker stop modapto-predictive-maintenace
    ```

## API

The deployed web service requires on input as defined below the ***SWAGGER_SERVER_URL***, which points to the URL of the deployed service for the Swagger Documentation.

The service exposes two endpoints under the **8000** port:

- **/predict (POST):** Enables up to 5 parallel algorithmic executions of *genetic_algorithm* and provides an output as shown above. The input, for now, are the user inputs, while the CORIM data and the algorithm parameters are the default ones.

- **/health (GET):** Implements a health check for the Web Service for monitoring purposes.

## Contributors

- Huu-Truong Le, Université de Lorraine
- Alkis Aznavouridis, Athens Technology Center (<a.aznavouridis@atc.gr>)
