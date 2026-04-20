from datetime import datetime

from openai.types.chat import ChatCompletionFunctionToolParam

"""
This file defines the tools and persona for an AI voice assistant.
To adapt this for your own business, you'll need to make changes in two key areas:

1. Customize the AI Persona:
   - Go to the `get_system_message()` function below.
   - Edit the text within the f-string to change the assistant's information (e.g.
     company name), its personality and its core instructions.
   - You can also update the tool descriptions within the prompt to better match
     your specific services.

2. Implement Real Tool Functions:
   - The async functions `search_knowledge_base`, `check_availability`, and
     `create_appointment` are currently mock implementations. They return fake data
     for demonstration purposes.
   - You must replace these functions or the mock logic inside these functions with
     your own backend integrations.

By making these changes, you can tailor this assistant to your specific business needs.
"""


def get_system_message(language: str) -> str:
    return f"""
You are a friendly, conversational AI voice assistant for 'Soniox AutoWorks'. \
Your primary goal is to help customers book car services and answer their questions.

Because this is a voice-to-voice conversation, you MUST keep your responses short, concise, and conversational. \
Avoid long paragraphs, lists, emojis, special characters, or complex sentences. Get straight to the point in a friendly tone.

Your role is to help users with appointments and answer questions about the shop. Use your tools to perform actions.

- To find answers to questions about business hours, services, location or policies, use the `search_knowledge_base` tool.
- To check for open appointment times for a specific service, use the `check_availability` tool.
- To book a new service appointment, use the `create_appointment` tool.

Start the conversation by greeting the user. User selected the following language for the conversation: {language}


Current date: {datetime.now().isoformat()}
"""


search_knowledge_base_tool_description = ChatCompletionFunctionToolParam(
    type="function",
    function={
        "name": "search_knowledge_base",
        "description": (
            "Searches the shop's knowledge base for information on services, "
            "business hours, location, and policies. Query the database in English, "
            "but respond in the user's language."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The user's question, e.g., 'What are your business hours?' "
                        "or 'Do you offer synthetic oil changes?'"
                    ),
                },
            },
            "required": ["query"],
        },
    },
)


async def search_knowledge_base(query: str) -> dict:
    """
    Simulates searching an internal database.
    In a real application this would search for an answer, given the query from the
    user in your knowledge base.
    """

    print(f"Running Tool: search_knowledge_base(query='{query}')")

    # Fictional knowledge base for the car mechanic shop
    mock_response = """
Soniox AutoWorks is located at 456 Gearshift Avenue.
We are open from 8 AM to 6 PM, Monday through Friday, and 9 AM to 2 PM on Saturdays. We are closed on Sundays.
We offer a range of services including:
- Standard, Synthetic-Blend, and Full-Synthetic Oil Changes. A standard oil change starts at $49.99.
- Tire Rotation and Balancing.
- Brake Inspection and Replacement.
- Engine Diagnostics and Repair.
We specialize in all major domestic and import brands.
    """

    return {
        "info": mock_response,
    }


check_availability_tool_description = ChatCompletionFunctionToolParam(
    type="function",
    function={
        "name": "check_availability",
        "description": "Checks available appointment slots for a specific service on a given day.",
        "parameters": {
            "type": "object",
            "properties": {
                "service_type": {
                    "type": "string",
                    "description": "The type of service the user wants to book.",
                    "enum": [
                        "oil_change",
                        "tire_rotation",
                        "brake_inspection",
                        "diagnostic",
                        "other",
                    ],
                },
                "date": {
                    "type": "string",
                    "description": "The date to check for availability, in YYYY-MM-DD format.",
                },
            },
            "required": ["service_type", "date"],
            "additionalProperties": False,
        },
    },
)


async def check_availability(service_type: str, date: str) -> dict:
    """
    Simulates checking a calendar for open appointment slots for a specific service.
    """
    print(
        f"Running Tool: check_availability(service_type='{service_type}', date='{date}')"
    )

    try:
        # For this demo, we'll generate some plausible random slots.
        # A real implementation would query a scheduling database.
        requested_date = datetime.strptime(date, "%Y-%m-%d").date()
        if requested_date < datetime.now().date():
            return {"error": "Sorry, I can't check for availability on a past date."}

        # Different services have different slot availability
        if service_type == "oil_change":
            slots = ["09:00", "09:30", "10:00", "10:30", "14:30", "15:00"]
        elif service_type == "tire_rotation":
            slots = ["09:00", "11:00", "14:00", "16:00"]
        else:
            slots = ["10:00", "13:00"]

        return {
            "date": date,
            "service_type": service_type,
            "available_slots": slots,
        }

    except ValueError:
        return {"error": "Invalid date format. Please use YYYY-MM-DD."}


create_appointment_tool_description = ChatCompletionFunctionToolParam(
    type="function",
    function={
        "name": "create_appointment",
        "description": "Books a new service appointment for a user with their vehicle details.",
        "parameters": {
            "type": "object",
            "properties": {
                "full_name": {
                    "type": "string",
                    "description": "The full name of the person booking the appointment.",
                },
                "phone_number": {
                    "type": "string",
                    "description": "The phone number of the person for confirmation texts.",
                },
                "service_type": {
                    "type": "string",
                    "description": "The type of service to book.",
                    "enum": [
                        "oil_change",
                        "tire_rotation",
                        "brake_inspection",
                        "diagnostic",
                        "other",
                    ],
                },
                "date": {
                    "type": "string",
                    "description": "The appointment date in YYYY-MM-DD format.",
                },
                "time": {
                    "type": "string",
                    "description": "The appointment time in HH:MM (24-hour) format.",
                },
                "vehicle_info": {
                    "type": "string",
                    "description": "The vehicle's year, make, and model, e.g., '2021 Ford Bronco'.",
                },
            },
            "required": [
                "full_name",
                "phone_number",
                "service_type",
                "date",
                "time",
                "vehicle_info",
            ],
            "additionalProperties": False,
        },
    },
)


async def create_appointment(
    full_name: str,
    phone_number: str,
    service_type: str,
    date: str,
    time: str,
    vehicle_info: str,
) -> dict:
    """
    Simulates booking the service appointment in the shop's system.
    """
    print(
        (
            "Running Tool: create_appointment("
            f"full_name='{full_name}', "
            f"service_type='{service_type}', "
            f"vehicle='{vehicle_info}' "
            f"date='{date}', "
            f"time='{time}')"
        )
    )

    if not all([full_name, phone_number, service_type, date, time, vehicle_info]):
        return {"success": False, "error": "Missing required information for booking."}

    return {
        "success": True,
        "full_name": full_name,
        "service_type": service_type,
        "vehicle_info": vehicle_info,
        "date": date,
        "time": time,
    }


def get_tools():
    """Tool description and function pairs for the LLM."""
    return [
        (
            check_availability_tool_description,
            check_availability,
        ),
        (
            create_appointment_tool_description,
            create_appointment,
        ),
        (
            search_knowledge_base_tool_description,
            search_knowledge_base,
        ),
    ]
