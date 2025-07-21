# Predictive Maintenance API

## Service Description

This FastAPI service provides predictive maintenance scheduling capabilities within the MODAPTO ecosystem. The service offers two distinct maintenance algorithms:

1. **Grouping Maintenance (PdM1)**: Uses genetic algorithms to optimize maintenance scheduling for component groups
2. **Threshold-Based Maintenance (PdM2)**: Analyzes failure patterns to provide maintenance recommendations based on configurable thresholds

**Response Formats:**

- **Grouping Maintenance**: Returns immediate success message, results published asynchronously to Kafka
- **Threshold-Based Maintenance**: Returns Base64-encoded JSON in the format: `{"result": "[Base64EncodedJSON]"}`

## Algorithms Overview

### 1. Grouping Maintenance Algorithm (PdM1)

**Location:** `algorithm/algorithm.py`  
**Purpose:** Optimizes maintenance scheduling by grouping components to minimize total costs
**Description:** This service provides predictive maintenance scheduling capabilities within the MODAPTO ecosystem. The purpose of the service is to provide an optimal scheduling of the maintenance action to be performed on a line or system. The output of the service will be for a list of maintenance actions and time to be performed for each component/group of components.

**Key Features:**

- Uses genetic algorithm optimization with configurable parameters
- Considers setup costs, downtime costs, and available repairmen
- Groups components for maintenance to reduce overall costs
- Outputs both individual and grouped maintenance plans
- Calculates cost savings from grouping strategy
- **Asynchronous processing**: Returns immediate confirmation, publishes results to Kafka
- **Event-driven**: Results published to `smart-service-event` topic

**Algorithm Parameters:**

- `genome_length`: Based on number of components (default: 10)
- `population_size`: 50 individuals
- `generations`: 100 iterations
- `crossover_probability`: 0.5 - 0.9 (adaptive)
- `mutation_probability`: 0.01 - 0.1 (adaptive)
- `time_window`: 0.0 - 1000.0 time units

**Input Requirements:**

- Component data with Alpha/Beta parameters, MTBF, maintenance duration
- Setup cost and downtime cost rate
- Number of available repairmen
- Smart service and production module identifiers (for Kafka Event Messages)

### 2. Threshold-Based Maintenance Algorithm (PdM2)

**Location:** `threshold-based_maintenance/PdM2_service.py`  
**Purpose:** Analyzes failure patterns to recommend maintenance actions based on failure frequency

**Key Features:**

- Analyzes historical failure events within configurable time windows
- Compares failure counts against inspection and replacement thresholds
- Identifies most critical components based on failure frequency
- Provides specific maintenance recommendations (inspection/replacement)
- Considers multiple time periods for comprehensive analysis

**Algorithm Parameters:**

- `window_size`: Analysis period in days (e.g., 90 days)
- `inspection_threshold`: Minimum failures to trigger inspection recommendation
- `replacement_threshold`: Minimum failures to trigger replacement recommendation
- `winds_count_component_replac`: Multiple of window_size for extended analysis (default: 3)

**Input Requirements:**

- Historical failure events with timestamps, failure types, and descriptions (CORIM Data)
- Analysis parameters (module ID, component IDs, thresholds)

## API Endpoints

### 1. Grouping Maintenance Endpoint (PdM1)

**POST** `/predict/grouping-maintenance`

Uses genetic algorithms to optimize maintenance scheduling for component groups. **Returns immediately** and processes results asynchronously, publishing to Kafka.

**Tags:** `["Grouping Maintenance", "PdM1"]`

#### Response

```json
{
    "message": "Grouping maintenance algorithm has been successfully initialized"
}
```

**Kafka Event Publishing:**

- Topic: `smart-service-event`
- Event includes full algorithm results with maintenance recommendations
- Published asynchronously after algorithm completion

#### Grouping Maintenance Request Body

```json
{
    "setup_cost": 100.0,
    "downtime_cost_rate": 50.0,
    "no_repairmen": 3,
    "smartService": "service_id",
    "productionModule": "module_id",
    "components": [
        {
            "Component": "100203",
            "Module": "POSTE 05 : MONTAGE ENTRAINEURS",
            "Stage": "MU MOTG",
            "Cell": "LIGNE DE MONTAGE MOTG04",
            "Alpha": 5,
            "Beta": 16.0,
            "Average maintenance duration": 1.108,
            "MTBF": 173.298,
            "Last Maintenance Action Time": "2025-01-01 10:00:00"
        },
        {
            "Component": "100270",
            "Module": "POSTE 05 : MONTAGE ENTRAINEURS",
            "Stage": "MU MOTG",
            "Cell": "POSTE DE CONTRÔLE",
            "Alpha": 5,
            "Beta": 6.0,
            "Average maintenance duration": 3.849,
            "MTBF": 179.545,
            "Last Maintenance Action Time": "2025-01-01 10:00:00"
        }
    ]
}
```

#### Grouping Maintenance Field Descriptions

- `setup_cost`: Setup cost for maintenance operations (shared across grouped components)
- `downtime_cost_rate`: Cost rate per unit time of production downtime
- `no_repairmen`: Number of available maintenance personnel
- `smartService`: Identifier for the smart service requesting maintenance
- `productionModule`: Identifier for the production module being analyzed
- `components[]`: Array of components with maintenance parameters
  - `Component`: Unique component identifier
  - `Module`: Module name where component is located
  - `Stage`: Production stage identifier
  - `Cell`: Production cell identifier
  - `Alpha`: Weibull distribution alpha parameter
  - `Beta`: Weibull distribution beta parameter
  - `Average maintenance duration`: Expected maintenance time in hours
  - `MTBF`: Mean Time Between Failures in hours
  - `Last Maintenance Action Time`: ISO timestamp of last maintenance

### 2. Threshold-Based Maintenance Endpoint (PdM2)

**POST** `/predict/threshold-based-maintenance`

Analyzes failure patterns to provide maintenance recommendations based on configurable thresholds.

**Tags:** `["Threshold Based Maintenance", "PdM2"]`

#### Threshold-Based Maintenance Request Body

```json
{
    "events": [
        {
            "Stage": "LIGNE DE MONTAGE MOTG04",
            "Cell": 100000,
            "Module": 100019,
            "Component": 100020,
            "Failure type (electrical/mechanical)": "Mechanic",
            "Failure description": "ascenseur ne monte pas retournement",
            "Maintenance action performed": "Réglage capteur sorti indexeur",
            "Component replacement (yes/no)": "no",
            "Name of worker": "Carlos M",
            "TS Intervention started": "16/06/2023 06:38:18"
        },
        {
            "Stage": "LIGNE DE MONTAGE IMS MOTG",
            "Cell": 100000,
            "Module": 100019,
            "Component": 100312,
            "Failure type (electrical/mechanical)": "Mechanic",
            "Failure description": "Donner suite à la panne sur les rippeurs",
            "Maintenance action performed": "Intervention réalisée le 22 novembre 2023",
            "Component replacement (yes/no)": "no",
            "Name of worker": "Carlos M",
            "TS Intervention started": "08/11/2023 10:13:56"
        }
    ],
    "parameters": {
        "module_ID": 100019,
        "components_ID": [100020, 100021, 100022, 100023, 100024],
        "window_size": 90,
        "inspection_threshold": 3,
        "replacement_threshold": 7
    }
}
```

#### Threshold-Based Maintenance Field Descriptions

- `events[]`: Array of historical failure events
  - `Stage`: Production stage where failure occurred
  - `Cell`: Cell identifier where failure occurred
  - `Module`: Module identifier where failure occurred
  - `Component`: Component identifier that failed
  - `Failure type (electrical/mechanical)`: Classification of failure type
  - `Failure description`: Detailed description of the failure
  - `Maintenance action performed`: Description of corrective action taken
  - `Component replacement (yes/no)`: Whether component was replaced
  - `Name of worker`: Maintenance worker who performed the action
  - `TS Intervention started`: Timestamp when intervention began
- `parameters`: Analysis configuration
  - `module_ID`: Target module for analysis
  - `components_ID`: List of component IDs to analyze
  - `window_size`: Analysis window in days
  - `inspection_threshold`: Failure count triggering inspection recommendation
  - `replacement_threshold`: Failure count triggering replacement recommendation

### 3. Health Check Endpoint

**GET** `/health`

Returns the API health status.

#### Health Response

```json
{
    "status": "healthy"
}
```

## API Response Formats

### Grouping Maintenance Response

Returns immediate confirmation message:

```json
{
    "message": "Grouping maintenance algorithm has been successfully initialized"
}
```

**Kafka Event Structure** (published to `smart-service-event` topic):

```json
{
    "description": "Grouping maintenance optimization completed",
    "module": "production_module_id",
    "timestamp": "2025-01-21T10:30:45",
    "priority": "HIGH",
    "eventType": "Maintenance Optimization",
    "sourceComponent": "Prognostics",
    "smartService": "smart_service_id",
    "topic": "smart-service-event",
    "results": {
        "Cost savings": 101.42,
        "Grouping maintenance": {
            "Group 1": [...]
        },
        "Individual maintenance": {
            "Group 1": [...]
        },
        "Time window": {
            "Begin": 0.0,
            "End": 1000.0
        }
    }
}
```

### Threshold-Based Maintenance Response

Returns Base64-encoded JSON:

```json
{
    "result": "eyJyZWNvbW1lbmRhdGlvbiI6ICJzY2hlZHVsZSBhbiBpbnNwZWN0aW9uIG9mIHN1YiBlbGVtZW50IDEwMDAyMCIsICJkZXRhaWxzIjogIml0IGZhaWxlZCA1IHRpbWVzIGluIHRoZSBsYXN0IDkwIGRheXMuIn0="
}
```

### Decoding Threshold Response

1. Extract the `result` field from the JSON response
2. Base64 decode the string value
3. Parse the resulting JSON string

### Threshold Response (decoded)

```json
{
    "Cost savings": 101.42,
    "Grouping maintenance": {
        "Group 1": [
            {
                "Component ID": 100203,
                "Component name": "POSTE 05 : MONTAGE ENTRAINEURS",
                "Replacement time": 349.571,
                "Duration": 4.957
            },
            {
                "Component ID": 100270,
                "Component name": "POSTE DE CONTRÔLE", 
                "Replacement time": 349.571,
                "Duration": 4.957
            }
        ]
    },
    "Individual maintenance": {
        "Group 1": [
            {
                "Component ID": 100203,
                "Component name": "POSTE 05 : MONTAGE ENTRAINEURS",
                "Replacement time": 173.298,
                "Duration": 1.108
            }
        ],
        "Group 2": [
            {
                "Component ID": 100270,
                "Component name": "POSTE DE CONTRÔLE",
                "Replacement time": 179.545,
                "Duration": 3.849
            }
        ]
    },
    "Time window": {
        "Begin": 0.0,
        "End": 1000.0
    }
}
```

**Response Fields:**

- `Cost savings`: Total cost reduction achieved by grouping maintenance activities
- `Grouping maintenance`: Optimized maintenance plan with components grouped together
- `Individual maintenance`: Alternative plan with each component maintained individually
- `Time window`: Analysis time frame for maintenance scheduling

### Threshold-Based Maintenance Response (decoded)

```json
{
    "recommendation": "schedule an inspection of sub element 100020",
    "details": "it failed 5 times in the last 90 days."
}
```

**Response Fields:**

- `recommendation`: Specific maintenance action recommended ("non", "inspection", or "replacement")
- `details`: Explanation of the recommendation with failure statistics

## Running the API

### Docker

```bash
docker build -t predictive-maintenance-api .
docker run -p 8000:8000 predictive-maintenance-api
```

## Environment Variables

- `CORS_DOMAINS`: Comma-separated list of allowed CORS domains (default: "<http://localhost:8094>")
- `SWAGGER_SERVER_URL`: Server URL for OpenAPI documentation (default: "<http://localhost:8000>")
- `KAFKA_BROKER`: Kafka broker address for event publishing (default: "<kafka.modapto.atc.gr:9092>")

## API Documentation

Once the API is running, you can access:

- **Interactive API docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)  
- **OpenAPI JSON schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Implementation Details

### Thread Pool Execution

Both maintenance algorithms use ThreadPoolExecutor for CPU-bound processing to prevent blocking the async event loop:

- Maximum workers: 5
- Managed via FastAPI lifespan events
- Ensures proper resource cleanup on shutdown

### Error Handling

- HTTP 500 responses with detailed error messages for algorithm failures
- Proper exception handling with contextual information
- Graceful degradation for invalid input data

### CORS Configuration

- Configurable via environment variables
- Supports multiple domain origins
- Enables credentials and all HTTP methods for development flexibility
