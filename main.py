from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
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
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log") if os.path.exists("/app") else logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import modules with error handling
try:
    # Import the genetic algorithm and output function from the algorithm module - PdM1
    from algorithm.algorithm import async_processing_grouping_maintenance_request
    logger.info("Successfully imported algorithm module")
except ImportError as e:
    logger.error(f"Failed to import algorithm module: {e}")
    async_processing_grouping_maintenance_request = None

try:
    # Import EventsProducer for Kafka integration
    from integration.EventsProducer import EventsProducer
    logger.info("Successfully imported EventsProducer")
except ImportError as e:
    logger.error(f"Failed to import EventsProducer: {e}")
    EventsProducer = None

try:
     # Import the PdM2 service class for threshold-based maintenance
    import sys
    import os
    # Add the threshold-based_maintenance directory to Python path
    threshold_dir = os.path.join(os.path.dirname(__file__), 'threshold-based_maintenance')
    if threshold_dir not in sys.path:
        sys.path.append(threshold_dir)
    from PdM2_service import PdM2Service
    logger.info("Successfully imported PdM2Service")
except ImportError as e:
    logger.error(f"Failed to import PdM2Service: {e}")
    PdM2Service = None

# Create a thread pool executor for parallel processing
executor = ThreadPoolExecutor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up FastAPI application...")
    app.state.executor = ThreadPoolExecutor(max_workers=5)
    logger.info("Application startup complete")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    app.state.executor.shutdown()
    logger.info("Application shutdown complete")

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

@app.middleware("http")
async def handle_http2_upgrade(request: Request, call_next):
    """
    Handle HTTP/2 upgrade requests based on deployment scheme.
    Returns 426 for upgrade requests when running on HTTP (localhost).
    """
    # Get scheme from environment or request
    scheme = os.getenv("SERVER_SCHEME", "https").lower()  # Default to http for localhost
    upgrade_header = request.headers.get("upgrade", "").lower()
    
    # If running on HTTP and client requests h2c upgrade, return 426
    if scheme == "http" and upgrade_header in ["h2c", "http/2"]:
        logger.warning(f"Rejecting HTTP/2 upgrade request on HTTP scheme: {upgrade_header}")
        return Response(
            content="HTTP/2 not supported over HTTP. Please retry with HTTP/1.1",
            status_code=426,
            headers={
                "Upgrade": "HTTP/1.1",
                "Connection": "Upgrade"
            }
        )
    
    # Otherwise, continue with the request
    response = await call_next(request)
    return response

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log basic request info
    logger.info(f"=== INCOMING HTTP REQUEST ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Log raw request body for POST requests to our endpoints
    if request.method == "POST" and any(path in str(request.url) for path in ["/predict/grouping-maintenance", "/predict/threshold-based-maintenance"]):
        body = await request.body()
        logger.info(f"Raw request body length: {len(body)}")
        logger.info(f"Raw request body (first 500 chars): {body[:500].decode('utf-8', errors='ignore')}")
        
        # FastAPI consumes the request body, so we need to set it back for the actual handler
        async def receive():
            return {"type": "http.request", "body": body}
        
        request._receive = receive
    
    response = await call_next(request)
    logger.info(f"Response status code: {response.status_code}")
    return response

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

def decode_base64_to_dict(base64_string: str) -> Dict[str, Any]:
    """
    Decode a Base64 string to a dictionary.
    """
    try:
        json_bytes = base64.b64decode(base64_string.encode("utf-8"))
        return json.loads(json_bytes.decode("utf-8"))
    except Exception as e:
        logger.error(f"Error decoding Base64 string: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid Base64 encoded request: {str(e)}")

# ---- Input Models ----
class ComponentData(BaseModel):
    Module: str = Field(..., alias="Module", description="Module name")
    Module_ID: str = Field(...,  alias="Module ID", description="Module identifier")
    Stage: str = Field(..., description="Stage name")
    Cell: str = Field(..., description="Cell name")
    Alpha: int = Field(..., description="Alpha parameter")
    Beta: float = Field(..., description="Beta parameter")
    Average_maintenance_duration: float = Field(..., alias="Average maintenance duration", description="Average maintenance duration")
    MTBF: float = Field(..., description="Mean Time Between Failures")
    Last_Maintenance_Action_Time: str = Field(..., alias="Last Maintenance Action Time", description="Last maintenance timestamp in ISO format")
    
    model_config = {"populate_by_name": True}

class GroupingMaintenanceInput(BaseModel):
    setupCost: float = Field(..., gt=0, description="Setup cost for maintenance operations")
    downtimeCostRate: float = Field(..., gt=0, description="Cost rate of downtime during maintenance")
    noRepairmen: int = Field(..., gt=0, description="Number of available repairmen")
    smartServiceId: str = Field(..., description="Smart service identifier")
    moduleId: str = Field(..., description="MODAPTO module identifier")
    components: List[ComponentData] = Field(..., description="List of components with their maintenance data")
    timeWindowStart: str = Field(..., description="Time window start in ISO format (e.g., '2025-09-01T00:00:00')")
    timeWindowEnd: str = Field(..., description="Time window end in ISO format (e.g., '2025-09-30T00:00:00')")

class FailureEvent(BaseModel):
    Stage: str = Field(..., description="Stage name")
    Cell: str = Field(..., description="Cell identifier")
    Module: str = Field(..., alias="Module ID",description="Module identifier")
    Component: str = Field(..., alias="Component ID", description="Component identifier")
    Failure_type: str = Field(..., alias="Failure Type (electrical/mechanical)", description="Type of failure")
    Failure_description: str = Field(..., alias="Failure description", description="Description of the failure")
    Maintenance_action_performed: str = Field(..., alias="Maintenance Action performed", description="Maintenance action taken")
    Component_replacement: str = Field(..., alias="Component replacement (yes/no)", description="Whether component was replaced")
    Name_of_worker: str = Field(..., alias="Name", description="Worker name")
    TS_Intervention_started: str = Field(..., alias="TS Intervention started", description="Intervention start timestamp")
    
    model_config = {"populate_by_name": True}

class ThresholdParameters(BaseModel):
    module_ID: int = Field(..., description="Module identifier")
    components_ID: List[int] = Field(..., description="List of component identifiers")
    window_size: int = Field(..., description="Analysis window size in days")
    inspection_threshold: int = Field(..., description="Threshold for inspection recommendation")
    replacement_threshold: int = Field(..., description="Threshold for replacement recommendation")

class ThresholdMaintenanceInput(BaseModel):
    smartServiceId: str = Field(..., description="Smart service identifier")
    moduleId: str = Field(..., description="Production module identifier")
    events: List[FailureEvent] = Field(..., description="List of failure events")
    parameters: ThresholdParameters = Field(..., description="Analysis parameters")

# ---- Output Models ----
class Component(BaseModel):
    """Model for a single component in a maintenance group"""
    Module_ID: str = Field(..., alias="Module ID", description="Unique identifier for the module")
    Module: str = Field(..., description="Name of the module")
    Replacement_time: float = Field(..., alias="Replacement time", description="Time at which the component is replaced")
    Duration: float = Field(..., description="Duration of the maintenance operation")
    
    model_config = {"populate_by_name": True}

class TimeWindow(BaseModel):
    """Time window for the maintenance schedule"""
    Begin: str = Field(..., description="Start time of the maintenance window in ISO format")
    End: str = Field(..., description="End time of the maintenance window in ISO format")

class GroupingMaintenanceOutput(BaseModel):
    """Full grouping maintenance schedule output"""
    Cost_savings: float = Field(..., alias="Cost savings", description="Total cost savings from the maintenance optimization")
    Grouping_maintenance: Dict[str, List[Component]] = Field(..., alias="Grouping maintenance", 
                                                        description="Optimized grouping of maintenance activities")
    Individual_maintenance: Dict[str, List[Component]] = Field(..., alias="Individual maintenance", 
                                                          description="Individual maintenance activities")
    Time_window: TimeWindow = Field(..., alias="Time window", description="Time window for the maintenance schedule")
    
    model_config = {"populate_by_name": True}

class ThresholdBasedMaintenanceOutput(BaseModel):
    """Full threshold-based maintenance schedule output"""
    Recommendation: str = Field(..., description="Maintenance recommendation based on failure analysis")
    Duration: int = Field(..., description="Duration of maintenance")
    Sub_element_ID: str = Field(..., alias="Sub element ID", description="Identifier of the failed sub-element")
    Module_ID: int = Field(..., alias="Module ID", description="Module identifier")
    Cell: str = Field(..., description="Cell identifier")
    Details: str = Field(..., description="Details of the recommendation, including failure counts and periods")

    model_config = {"populate_by_name": True}

class Base64Request(BaseModel):
    """Unified input model for Base64 encoded requests"""
    request: str = Field(..., description="Base64 encoded JSON request data")

class Base64Response(BaseModel):
    """Unified response model for Base64 encoded results"""
    response: str = Field(..., description="Base64 encoded JSON result")                            
                                
# Async function to process grouping maintenance and publish to Kafka
async def process_grouping_maintenance_async(
    setup_cost: float,
    downtime_cost_rate: float,
    no_repairmen: int,
    components: List[ComponentData],
    smart_service: str,
    module: str,
    time_window_start: str,
    time_window_end: str):
    """
    Process grouping maintenance request asynchronously and publish results to Kafka.
    """
    try:
        # Parse datetime strings to datetime objects
        from datetime import datetime
        try:
            TW_start = datetime.fromisoformat(time_window_start.replace('Z', '+00:00'))
            TW_end = datetime.fromisoformat(time_window_end.replace('Z', '+00:00'))
            logger.info(f"Parsed time window: {TW_start} to {TW_end}")
        except ValueError as e:
            logger.error(f"Invalid datetime format: {str(e)}")
            raise ValueError(f"Invalid datetime format. Use ISO format like '2025-09-01T00:00:00': {str(e)}")
        
        # Convert ComponentData objects to simple list for the algorithm
        component_list = [component.model_dump(by_alias=True) for component in components]
        
        # Parse Last Maintenance Action Time strings to datetime objects for each component
        for comp in component_list:
            if "Last Maintenance Action Time" in comp:
                try:
                    comp["Last Maintenance Action Time"] = datetime.fromisoformat(
                        comp["Last Maintenance Action Time"].replace('Z', '+00:00')
                    )
                except ValueError as e:
                    logger.error(f"Invalid datetime format in component {comp.get('Module ID', 'unknown')}: {str(e)}")
                    raise ValueError(f"Invalid datetime format in component data: {str(e)}")
        
        # Log component structure after model_dump for debugging
        if component_list:
            logger.info(f"First component keys after model_dump: {list(component_list[0].keys())}")
            logger.debug(f"First component data: {component_list[0]}")
        
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
                module,
                TW_start,
                TW_end
            )
        )
        
        # Get Kafka broker from environment variable and publish event
        kafka_broker = os.getenv("KAFKA_BROKER", "kafka:9092")
        producer = EventsProducer(kafka_broker)
        
        # Publish event (success or error) to Kafka topic
        producer.produce_event("grouping-predictive-maintenance", event_data)
        
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
                "module": module,
                "timestamp": datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "priority": "HIGH",
                "eventType": "Critical Processing Error",
                "sourceComponent": "Predictive Maintenance",
                "smartService": smart_service,
                "topic": "grouping-predictive-maintenance",
                "results": None
            }
            
            producer.produce_event("grouping-predictive-maintenance", critical_error_event)
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
    # Create input data structure for PdM2Service (excluding smartService and module)
    # Use by_alias=True to preserve original field names from the JSON
    input_data = {
        "events": [event.model_dump(by_alias=True) for event in data.events],
        "parameters": data.parameters.model_dump(by_alias=True)
    }
    logger.info("Processing threshold-based maintenance request")
    logger.info(f"Input data keys: {list(input_data.keys()) if input_data else 'None'}")
    logger.debug(f"First event fields: {list(input_data['events'][0].keys()) if input_data.get('events') else 'No events'}")
    return _process_threshold_maintenance_core(input_data)

# Core function for threshold maintenance processing
def _process_threshold_maintenance_core(input_data):
    """
    Core processing function for PdM2Service.
    """
    # Initialize PdM2 service with input data
    pdm2_service = PdM2Service(
        input_data=input_data
    )
    
    # Run analysis and return result
    return pdm2_service.run()

# ---- Main Endpoints ----
@app.post("/predict/threshold-based-maintenance", response_model=Base64Response, tags=["Threshold Based Maintenance (PdM2)"])
async def predict_threshold_based_maintenance(base64_data: Base64Request):
    """
    Predictive maintenance algorithm endpoint for Threshold-Based maintenance.
    This endpoint accepts a Base64 encoded JSON request and uses the PdM2 service for threshold-based analysis.
    
    Request format: {"request": "base64_encoded_json_data"}
    """
    if PdM2Service is None:
        logger.warning("PdM2Service not available - module import failed")
        raise HTTPException(status_code=503, detail="PdM2 service is not available due to import errors")
    
    try:
        logger.info("=== THRESHOLD-BASED MAINTENANCE REQUEST RECEIVED ===")
        logger.info(f"Raw Base64 request length: {len(base64_data.request) if base64_data.request else 'None'}")
        
        # Log first 200 characters of Base64 data for debugging (not full data for security)
        if base64_data.request:
            logger.debug(f"Base64 request preview: {base64_data.request[:200]}...")
        
        # Decode Base64 request
        decoded_data = decode_base64_to_dict(base64_data.request)
        logger.info("Successfully decoded Base64 request")
        logger.info(f"Decoded data keys: {list(decoded_data.keys()) if decoded_data else 'None'}")
        logger.debug(f"Decoded data structure: {json.dumps(decoded_data, indent=2, default=str)}")
        
        # Parse decoded data into ThresholdMaintenanceInput model
        try:
            logger.info("Attempting to parse decoded data into ThresholdMaintenanceInput model")
            data = ThresholdMaintenanceInput(**decoded_data)
            logger.info(" Successfully parsed request data")
            logger.info(f"Request summary - Events count: {len(data.events)}, "
                       f"Smart Service: {data.smartServiceId}, Module: {data.moduleId}")
        except Exception as e:
            logger.error(" Failed to parse decoded data into model")
            logger.error(f"Validation error details: {str(e)}")
            logger.error(f"Validation error type: {type(e).__name__}")
            
            # Log specific field validation issues if it's a Pydantic validation error
            if hasattr(e, 'errors'):
                logger.error("Detailed validation errors:")
                for error in e.errors():
                    logger.error(f"  Field: {error.get('loc', 'unknown')}")
                    logger.error(f"  Error: {error.get('msg', 'unknown')}")
                    logger.error(f"  Input: {error.get('input', 'unknown')}")
            
            raise HTTPException(status_code=422, detail=f"Request validation failed: {str(e)}")
        
        # Use ThreadPoolExecutor for CPU-bound tasks
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            app.state.executor,
            partial(
                process_threshold_maintenance_request,
                data
            )
        )
        logger.info(f"Raw result from PdM2Service: {json.dumps(result, indent=2, default=str)}")
        # Validate Result
        threshold_result = ThresholdBasedMaintenanceOutput(**result)
        
        # Encode response to Base64
        encoded_result = encode_output_to_base64(threshold_result.model_dump(by_alias=True))
        logger.info("Successfully processed threshold-based maintenance request")
        
        return Base64Response(response=encoded_result)
    except HTTPException:
        # Re-raise HTTP exceptions (400, 503)
        raise
    except Exception as e:
        logger.error(f"Error in threshold-based maintenance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while executing the threshold-based maintenance algorithm: {str(e)}")
    
@app.post("/predict/grouping-maintenance", tags=["Grouping Predictive Maintenance (PdM1)"])
async def predict_grouping_maintenance(base64_data: Base64Request):
    """
    Predictive maintenance algorithm endpoint for Grouping Maintenance.
    This endpoint accepts a Base64 encoded JSON request, initializes the genetic algorithm asynchronously and publishes results to Kafka.
    
    Request format: {"request": "base64_encoded_json_data"}
    """
    # Log raw incoming request FIRST - before any validation
    logger.info("=== RAW GROUPING MAINTENANCE REQUEST RECEIVED ===")
    logger.info(f"Request type: {type(base64_data)}")
    logger.info(f"Request attributes: {dir(base64_data)}")
    
    if hasattr(base64_data, 'request'):
        logger.info(f"base64_data.request exists: {base64_data.request is not None}")
        logger.info(f"base64_data.request type: {type(base64_data.request)}")
        logger.info(f"base64_data.request length: {len(base64_data.request) if base64_data.request else 'None'}")
        if base64_data.request:
            logger.info(f"Base64 request preview (first 100 chars): {base64_data.request[:100]}")
    else:
        logger.error("base64_data.request attribute missing!")
    
    # Log the entire raw request object
    try:
        logger.info(f"Raw request object: {base64_data}")
        logger.info(f"Raw request dict: {base64_data.model_dump() if hasattr(base64_data, 'model_dump') else 'No model_dump method'}")
    except Exception as e:
        logger.error(f"Error logging raw request: {str(e)}")
    
    if async_processing_grouping_maintenance_request is None:
        logger.warning("Grouping maintenance algorithm not available - module import failed")
        raise HTTPException(status_code=503, detail="Grouping maintenance service is not available due to import errors")
    
    try:
        logger.info("=== STARTING REQUEST PROCESSING ===")
        
        # Validate base64_data.request exists before proceeding
        if not hasattr(base64_data, 'request') or base64_data.request is None:
            logger.error("Request validation failed: base64_data.request is missing or None")
            raise HTTPException(status_code=400, detail="Missing 'request' field in Base64Request")
        
        # Decode Base64 request
        decoded_data = decode_base64_to_dict(base64_data.request)
        logger.info("Successfully decoded Base64 request")
        logger.info(f"Decoded data keys: {list(decoded_data.keys()) if decoded_data else 'None'}")
        logger.debug(f"Decoded data structure: {json.dumps(decoded_data, indent=2, default=str)}")
        
        # Parse decoded data into GroupingMaintenanceInput model
        try:
            logger.info("Attempting to parse decoded data into GroupingMaintenanceInput model")
            data = GroupingMaintenanceInput(**decoded_data)
            logger.info("✓ Successfully parsed request data")
            logger.info(f"Request summary - Setup Cost: {data.setupCost}, Downtime Cost Rate: {data.downtimeCostRate}, "
                       f"Repairmen: {data.noRepairmen}, Components: {len(data.components)}, "
                       f"Smart Service: {data.smartServiceId}, Module: {data.moduleId}, "
                       f"Time Window: {data.timeWindowStart} to {data.timeWindowEnd}")
        except Exception as e:
            logger.error("✗ Failed to parse decoded data into model")
            logger.error(f"Validation error details: {str(e)}")
            logger.error(f"Validation error type: {type(e).__name__}")
            
            # Log specific field validation issues if it's a Pydantic validation error
            if hasattr(e, 'errors'):
                logger.error("Detailed validation errors:")
                for error in e.errors():
                    logger.error(f"  Field: {error.get('loc', 'unknown')}")
                    logger.error(f"  Error: {error.get('msg', 'unknown')}")
                    logger.error(f"  Input: {error.get('input', 'unknown')}")
            
            raise HTTPException(status_code=422, detail=f"Request validation failed: {str(e)}")
            
        # Start the async algorithm processing (fire and forget)
        asyncio.create_task(process_grouping_maintenance_async(
            data.setupCost,
            data.downtimeCostRate,
            data.noRepairmen,
            data.components,
            data.smartServiceId,
            data.moduleId,
            data.timeWindowStart,
            data.timeWindowEnd
        ))
        
        logger.info("Successfully initialized grouping maintenance algorithm")
        return {"message": "Grouping maintenance algorithm has been successfully initialized"}
    except HTTPException:
        # Re-raise HTTP exceptions (400, 503)
        raise
    except Exception as e:
        logger.error(f"Error in grouping maintenance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while initializing the grouping maintenance algorithm: {str(e)}")

@app.get("/health" , tags=["Health Check"])
def health_check():
    """
    Health check endpoint for the API.
    """
    services_status = {
        "Grouping Predictive Maintenance": async_processing_grouping_maintenance_request is not None,
        "Kafka Events Producer": EventsProducer is not None,
        "Threshold-Based Predictive Maintenance": PdM2Service is not None
    }
    
    logger.info(f"Health check requested - Services status: {services_status}")
    
    return {
        "status": "healthy",
        "services": services_status,
        "message": "Predictive Maintenance API is running"
    }
