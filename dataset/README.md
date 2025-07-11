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

1. "component.json": Contains the parameters of the components within the production line (Equipment ID, Component name, Alpha, Beta, Average maintenance duration, Mean time between failure, Last Maintenance Action Time). With the format:

```sh
[
    {
        "Equipment ID": 0,
        "Component": "POSTE DE CONTRÔLE",
        "Alpha": 5,
        "Beta": 16.0,
        "Average maintenance duration": 1.108,
        "MTBF": 173.298,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 1,
        "Component": "CONNECTEURS",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 3.849,
        "MTBF": 179.545,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 2,
        "Component": "POSTE 09 : MONTAGE CÔTÉ A (RETOURNEMENTS)",
        "Alpha": 5,
        "Beta": 20.0,
        "Average maintenance duration": 0.726,
        "MTBF": 208.829,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 3,
        "Component": "POSTE 04  : EMMANCHEMENTS ROULEMENTS (PRESSE)",
        "Alpha": 5,
        "Beta": 20.0,
        "Average maintenance duration": 1.925,
        "MTBF": 548.357,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 4,
        "Component": "CONVOYEURS",
        "Alpha": 5,
        "Beta": 10.0,
        "Average maintenance duration": 0.492,
        "MTBF": 627.938,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 5,
        "Component": "LIGNE DE MONTAGE MOTG02",
        "Alpha": 5,
        "Beta": 7.2,
        "Average maintenance duration": 0.89,
        "MTBF": 732.33,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 6,
        "Component": "POSTE 02 : ENTRÉE PLATEAUX PLEIN",
        "Alpha": 5,
        "Beta": 12.0,
        "Average maintenance duration": 1.73,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 7,
        "Component": "POSTE 15 : CONTRÔLE HAUTE TENSION",
        "Alpha": 5,
        "Beta": 12.0,
        "Average maintenance duration": 1.082,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 8,
        "Component": "MAGASIN PLATEAUX VIDES",
        "Alpha": 5,
        "Beta": 8.0,
        "Average maintenance duration": 0.815,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 9,
        "Component": "ASCENSEUR DE SORTIE",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 0.709,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 10,
        "Component": "MM-TAILLE1",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 13.964,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 11,
        "Component": "ASCENSEUR",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 0.477,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 12,
        "Component": "KTM6",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 21.963,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 13,
        "Component": "PINCE",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 4.499,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 14,
        "Component": "POSTE 05 : MONTAGE ENTRAINEURS",
        "Alpha": 5,
        "Beta": 8.0,
        "Average maintenance duration": 3.307,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 15,
        "Component": "KTM5",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 2.632,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 16,
        "Component": "EMMANCHEMENT",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 2.263,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 17,
        "Component": "CHAUFFE VENTILATEURS",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 2.15,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 18,
        "Component": "ECRANS",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 2.024,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 19,
        "Component": "DIVERS",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 2.022,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 20,
        "Component": "EI7-BARRETTE",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 1.231,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 21,
        "Component": "POSTE 06A : MONTAGE FREINS + SERRAGE TIRANTS",
        "Alpha": 5,
        "Beta": 7.0,
        "Average maintenance duration": 1.109,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 22,
        "Component": "TRANSLATION",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 1.053,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 23,
        "Component": "CONVOYEUR CÔTÉ CONTRÔLE",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 0.971,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 24,
        "Component": "ASCENSEUR SORTIE",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 0.775,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 25,
        "Component": "VISSEUSES ÉLECTRIQUE",
        "Alpha": 5,
        "Beta": 6.0,
        "Average maintenance duration": 0.639,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 26,
        "Component": "POSTE 07 : MONTAGE CAPOT + SOUPAPES",
        "Alpha": 5,
        "Beta": 10.0,
        "Average maintenance duration": 0.572,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    },
    {
        "Equipment ID": 27,
        "Component": "POSTE 14 : CONTRÔLE MISE Á LA TERRE",
        "Alpha": 5,
        "Beta": 10.0,
        "Average maintenance duration": 0.371,
        "MTBF": ...,
        "Last Maintenance Action Time": ...
    }
]
```
***Note:***
- "MTBF":Mean time between failure of the component.
- "Last Maintenance Action Time": this information comes from the CORIM file by requesting the last maintenance action time for the ID component.
- There are some values in "MTBF" and "Last Maintenance Action Time" missing, this will be filled after discussing with SEW about this dataset format later.

2. "activity.json": Includes the parameter (Replacement time) related to maintenance activities in the production line and will be calculated from MTBF and Last Maintenance Action Time, with each activity mapped to its corresponding component (each row of activity has the corresponding Component ID). With the format:

```sh
{   
    "window":   {
                    "Begin": 0.0,
                    "End": 1000.0
                },
    "failure":  [
                    {
                        "ID activity": 1,
                        "Replacement time": 173.298,
                        "Equipment ID": 0
                    },
                    {
                        "ID activity": 2,
                        "Replacement time": 346.596,
                        "Equipment ID": 0
                    },
                    {
                        "ID activity": 3,
                        "Replacement time": 519.895,
                        "Equipment ID": 0
                    },
                    {
                        "ID activity": 4,
                        "Replacement time": 693.193,
                        "Equipment ID": 0
                    },
                    {
                        "ID activity": 5,
                        "Replacement time": 866.491,
                        "Equipment ID": 0
                    },
                    {
                        "ID activity": 6,
                        "Replacement time": 179.545,
                        "Equipment ID": 1
                    },
                    {
                        "ID activity": 7,
                        "Replacement time": 359.09,
                        "Equipment ID": 1
                    },
                    {
                        "ID activity": 8,
                        "Replacement time": 538.635,
                        "Equipment ID": 1

                    },
                    {
                        "ID activity": 9,
                        "Replacement time": 718.179,
                        "Equipment ID": 1
                    },
                    {
                        "ID activity": 10,
                        "Replacement time": 897.724,
                        "Equipment ID": 1
                    },
                    {
                        "ID activity": 11,
                        "Replacement time": 208.829,
                        "Equipment ID": 2
                    },
                    {
                        "ID activity": 12,
                        "Replacement time": 417.658,
                        "Equipment ID": 2
                    },
                    {
                        "ID activity": 13,
                        "Replacement time": 626.487,
                        "Equipment ID": 2
                    },
                    {
                        "ID activity": 14,
                        "Replacement time": 835.316,
                        "Equipment ID": 2
                    },
                    {
                        "ID activity": 15,
                        "Replacement time": 548.357,
                        "Equipment ID": 3
                    },
                    {
                        "ID activity": 16,
                        "Replacement time": 627.938,
                        "Equipment ID": 4
                    },
                    {
                        "ID activity": 17,
                        "Replacement time": 732.33,
                        "Equipment ID": 5
                    }
                ]
}
```
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
