from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Union
from datetime import datetime
from fastapi.openapi.utils import get_openapi
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import base64
import json

# Import the genetic algorithm and output function from the algorithm module - PdM1
from algorithm.algorithm import async_processing_grouping_maintenance_request

# Import EventsProducer for Kafka integration
from integration.EventsProducer import EventsProducer

# Import the PdM2 service class for threshold-based maintenance
from threshold_based_maintenance.PdM2_service import PdM2Service

# Create a thread pool executor for parallel processing
executor = ThreadPoolExecutor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.executor = ThreadPoolExecutor(max_workers=5)
    yield
    # Shutdown
    app.state.executor.shutdown()

app = FastAPI(
    title="Predictive Maintenance API",
    description="Optimize scheduling of maintenance actions for production components.",
    version="v1.0",
    lifespan=lifespan,
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

def encode_output_to_base64(output: Dict[str, Any]) -> str:
    """
    Encode a dictionary to a Base64 string.
    """
    json_bytes = json.dumps(output, default=str).encode("utf-8")
    return base64.b64encode(json_bytes).decode("utf-8")

# ---- Input Models ----
class ComponentData(BaseModel):
    Component: str = Field(..., description="Component identifier")
    Module: str = Field(..., description="Module name")
    Stage: str = Field(..., description="Stage name")
    Cell: str = Field(..., description="Cell name")
    Alpha: int = Field(..., description="Alpha parameter")
    Beta: float = Field(..., description="Beta parameter")
    Average_maintenance_duration: float = Field(..., alias="Average maintenance duration", description="Average maintenance duration")
    MTBF: float = Field(..., description="Mean Time Between Failures")
    Last_Maintenance_Action_Time: str = Field(..., alias="Last Maintenance Action Time", description="Last maintenance timestamp in ISO format")
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class GroupingMaintenanceInput(BaseModel):
    setup_cost: float = Field(..., gt=0, description="Setup cost for maintenance operations")
    downtime_cost_rate: float = Field(..., gt=0, description="Cost rate of downtime during maintenance")
    no_repairmen: int = Field(..., gt=0, description="Number of available repairmen")
    smartService: str = Field(..., description="Smart service identifier")
    productionModule: str = Field(..., description="Production module identifier")
    components: List[ComponentData] = Field(..., description="List of components with their maintenance data")

class FailureEvent(BaseModel):
    Stage: str = Field(..., description="Stage name")
    Cell: int = Field(..., description="Cell identifier")
    Module: int = Field(..., description="Module identifier")
    Component: int = Field(..., description="Component identifier")
    Failure_type: str = Field(..., alias="Failure type (electrical/mechanical)", description="Type of failure")
    Failure_description: str = Field(..., alias="Failure description", description="Description of the failure")
    Maintenance_action_performed: str = Field(..., alias="Maintenance action performed", description="Maintenance action taken")
    Component_replacement: str = Field(..., alias="Component replacement (yes/no)", description="Whether component was replaced")
    Name_of_worker: str = Field(..., alias="Name of worker", description="Worker name")
    TS_Intervention_started: str = Field(..., alias="TS Intervention started", description="Intervention start timestamp")
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class ThresholdParameters(BaseModel):
    module_ID: int = Field(..., description="Module identifier")
    components_ID: List[int] = Field(..., description="List of component identifiers")
    window_size: int = Field(..., description="Analysis window size in days")
    inspection_threshold: int = Field(..., description="Threshold for inspection recommendation")
    replacement_threshold: int = Field(..., description="Threshold for replacement recommendation")

class ThresholdMaintenanceInput(BaseModel):
    events: List[FailureEvent] = Field(..., description="List of failure events")
    parameters: ThresholdParameters = Field(..., description="Analysis parameters")

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

class GroupingMaintenanceOutput(BaseModel):
    """Full grouping maintenance schedule output"""
    Cost_savings: float = Field(..., alias="Cost savings", description="Total cost savings from the maintenance optimization")
    Grouping_maintenance: Dict[str, List[Component]] = Field(..., alias="Grouping maintenance", 
                                                        description="Optimized grouping of maintenance activities")
    Individual_maintenance: Dict[str, List[Component]] = Field(..., alias="Individual maintenance", 
                                                          description="Individual maintenance activities")
    Time_window: TimeWindow = Field(..., alias="Time window", description="Time window for the maintenance schedule")
    
    class Config:
        validate_by_name = True

class ThresholdBasedMaintenanceOutput(BaseModel):
    """Full threshold-based maintenance schedule output"""
    recommendation: str = Field(..., description="Maintenance recommendation based on failure analysis")
    details: str = Field(..., description="Details of the recommendation, including failure counts and periods")

    class Config:
        validate_by_name = True

class Base64Response(BaseModel):
    """Unified response model for Base64 encoded results"""
    result: str = Field(..., description="Base64 encoded JSON result")                            
                                
# Async function to process grouping maintenance and publish to Kafka
async def process_grouping_maintenance_async(
    setup_cost: float,
    downtime_cost_rate: float,
    no_repairmen: int,
    components: List[ComponentData],
    smart_service: str,
    production_module: str):
    """
    Process grouping maintenance request asynchronously and publish results to Kafka.
    """
    try:
        # Convert ComponentData objects to simple list for the algorithm
        component_list = [component.model_dump() for component in components]
        
        # Run the CPU-intensive algorithm in thread pool
        loop = asyncio.get_event_loop()
        event_data = await loop.run_in_executor(
            None,  # Use default thread pool
            partial(
                async_processing_grouping_maintenance_request,
                setup_cost,
                downtime_cost_rate,
                no_repairmen,
                component_list,
                smart_service,
                production_module
            )
        )
        
        # Get Kafka broker from environment variable and publish event
        kafka_broker = os.getenv("KAFKA_BROKER", "kafka:9092")
        producer = EventsProducer(kafka_broker)
        
        # Publish event (success or error) to Kafka topic
        producer.produce_event("smart-service-event", event_data)
        
        # Log appropriate message based on event type
        if 'Error' in event_data.get('eventType', ''):
            print("Error event regarding grouping maintenance published successfully!")
        else:
            print("Event regarding grouping maintenance published successfully!")
        
        producer.close()
        
    except Exception as e:
        print(f"Critical error in async grouping maintenance processing: {str(e)}")
        
        # Last resort: create and publish a critical error event
        try:
            kafka_broker = os.getenv("KAFKA_BROKER", "kafka.modapto.atc.gr:9092")
            producer = EventsProducer(kafka_broker)
            
            critical_error_event = {
                "description": f"Critical error in maintenance API processing: {str(e)}",
                "module": production_module,
                "timestamp": datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "priority": "HIGH",
                "eventType": "Critical Processing Error",
                "sourceComponent": "Predictive Maintenance",
                "smartService": smart_service,
                "topic": "smart-service-event",
                "results": None
            }
            
            producer.produce_event("smart-service-event", critical_error_event)
            producer.close()
            print("Critical error event published to Kafka!")
        except Exception as kafka_error:
            print(f"Failed to publish critical error event to Kafka: {str(kafka_error)}")

# Function to process threshold-based maintenance request
def process_threshold_maintenance_request(data):
    """
    Process threshold-based maintenance request using PdM2Service.
    This function is called by the threshold-based maintenance endpoint.
    """
    # Create input data structure for PdM2Service (excluding smartService and productionModule)
    input_data = {
        "events": [event.model_dump() for event in data.events],
        "parameters": data.parameters.model_dump()
    }
    
    return _process_threshold_maintenance_core(input_data)

# Core function for threshold maintenance processing
def _process_threshold_maintenance_core(input_data):
    """
    Core processing function for PdM2Service.
    """
    # Initialize PdM2 service with input data
    pdm2_service = PdM2Service(
        input_data=input_data,
        winds_count_component_replac=3,
        output_path="maintenance_recommendations.json"
    )
    
    # Run analysis and return result
    return pdm2_service.run()

# ---- Main Endpoints ----
@app.post("/predict/threshold-based-maintenance", response_model=Base64Response, tags=["Threshold Based Maintenance", "PdM2"])
async def predict_threshold_based_maintenance(data: ThresholdMaintenanceInput):
    """
    Predictive maintenance algorithm endpoint for Threshold-Based maintenance.
    This endpoint uses the PdM2 service for threshold-based analysis.
    """
    try:
        # Use ThreadPoolExecutor for CPU-bound tasks
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            app.state.executor,
            partial(
                process_threshold_maintenance_request,
                data
            )
        )
        
        # Encode response to Base64
        encoded_result = encode_output_to_base64(result)
        
        return Base64Response(result=encoded_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while executing the threshold-based maintenance algorithm: {str(e)}")
    
@app.post("/predict/grouping-maintenance", tags=["Grouping Maintenance", "PdM1"])
async def predict_grouping_maintenance(data: GroupingMaintenanceInput):
    """
    Predictive maintenance algorithm endpoint for Grouping Maintenance.
    This endpoint initializes the genetic algorithm asynchronously and publishes results to Kafka.
    """
    try:
        # Start the async algorithm processing (fire and forget)
        asyncio.create_task(process_grouping_maintenance_async(
            data.setup_cost,
            data.downtime_cost_rate,
            data.no_repairmen,
            data.components,
            data.smartService,
            data.productionModule
        ))
        
        return {"message": "Grouping maintenance algorithm has been successfully initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while initializing the grouping maintenance algorithm: {str(e)}")

@app.get("/health")
def health_check():
    """
    Health check endpoint for the API.
    """
    return {"status": "healthy"}