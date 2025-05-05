from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.openapi.utils import get_openapi
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
from functools import partial

# Import the genetic algorithm and output function from the algorithm module
from algorithm.algorithm import genetic_algorithm, format_output

# Create a thread pool executor for parallel processing
executor = ThreadPoolExecutor()

app = FastAPI(
    title="Predictive Maintenance API",
    description="Optimize scheduling of maintenance actions for production components.",
    version="1.0.0",
)

# Set the origins for CORS
def get_cors_origins():
    origins_string = os.getenv("CORS_DOMAINS", "http://localhost:8094") # Default DTM URL
    origins = origins_string.split(",")
    return [origin.strip() for origin in origins if origin.strip()]

# Custom OpenAPI schema to include server URL
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    server_url = os.getenv("SWAGGER_SERVER_URL", "http://localhost:8000")
    openapi_schema["servers"] = [{"url": server_url}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Input Model ----
class MaintenanceInput(BaseModel):
    setup_cost: float = Field(..., gt=0, description="Setup cost for maintenance operations")
    downtime_cost_rate: float = Field(..., gt=0, description="Cost rate of downtime during maintenance")
    no_repairmen: int = Field(..., gt=0, description="Number of available repairmen")

# ---- Output Models ----
class Component(BaseModel):
    """Model for a single component in a maintenance group"""
    Component_ID: int = Field(..., alias="Component ID", description="Unique identifier for the component")
    Component_name: str = Field(..., alias="Component name", description="Name of the component")
    Replacement_time: float = Field(..., alias="Replacement time", description="Time at which the component is replaced")
    Duration: float = Field(..., description="Duration of the maintenance operation")
    
    class Config:
        validate_by_name = True

class TimeWindow(BaseModel):
    """Time window for the maintenance schedule"""
    Begin: float = Field(..., description="Start time of the maintenance window")
    End: float = Field(..., description="End time of the maintenance window")

class MaintenanceOutput(BaseModel):
    """Full maintenance schedule output"""
    Cost_savings: float = Field(..., alias="Cost savings", description="Total cost savings from the maintenance optimization")
    Grouping_maintenance: Dict[str, List[Component]] = Field(..., alias="Grouping maintenance", 
                                                        description="Optimized grouping of maintenance activities")
    Individual_maintenance: Dict[str, List[Component]] = Field(..., alias="Individual maintenance", 
                                                          description="Individual maintenance activities")
    Time_window: TimeWindow = Field(..., alias="Time window", description="Time window for the maintenance schedule")
    
    class Config:
        validate_by_name = True

# Function to process a single request
def process_maintenance_request(
    setup_cost: float,
    downtime_cost_rate: float,
    no_repairmen: int):
    """
    Process a single maintenance request and return the result.
    This function is called by the predict_maintenance endpoint.
    """
    # Algorithm parameters
    genome_length = 10
    population_size = 50
    generations = 100
    p_c_min, p_c_max = 0.5, 0.9
    p_m_min, p_m_max = 0.01, 0.1
    t_begin, t_end = 0.0, 1000.0
    
    # Run the algorithm
    best_individual, best_fitness = genetic_algorithm(
        genome_length,
        no_repairmen,
        population_size,
        generations,
        p_c_min, p_c_max,
        p_m_min, p_m_max,
        setup_cost,
        downtime_cost_rate
    )
    
    # Formulate the JSON
    return format_output(best_individual, best_fitness, t_begin, t_end)

# ---- Main Endpoint ----
@app.post("/predict", response_model=MaintenanceOutput, tags=["Maintenance"])
async def predict_maintenance(data: MaintenanceInput):
    """
    Predictive maintenance algorithm endpoint.
    This endpoint accepts parameters for the genetic algorithm and returns the best individual and fitness.
    """
    try:
        # Use ThreadPoolExecutor for CPU-bound tasks (like your genetic algorithm)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            app.state.executor,
            partial(
                process_maintenance_request,
                data.setup_cost,
                data.downtime_cost_rate,
                data.no_repairmen
            )
        )
        
        # Return the result
        return MaintenanceOutput(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while executing the algorithm: {str(e)}")

@app.get("/health")
def health_check():
    """
    Health check endpoint for the API.
    """
    return {"status": "healthy"}

# Setup and teardown for the executor
@app.on_event("startup")
async def startup_event():
    app.state.executor = ThreadPoolExecutor(max_workers=5)

@app.on_event("shutdown")
async def shutdown_event():
    app.state.executor.shutdown()