import os
import pymongo
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MongoDB connection details
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://192.168.137.131:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "parkez")
MONGODB_VEHICLES_COLLECTION = os.getenv("MONGODB_VEHICLES_COLLECTION", "vehicles")
MONGODB_TICKETS_COLLECTION = os.getenv("MONGODB_TICKETS_COLLECTION", "tickets")

# Sample vehicle data
SAMPLE_VEHICLES = [
    {
        "vehicleNumber": "ABC123",
        "vehicleType": "car",
        "make": "Toyota",
        "model": "Corolla",
        "color": "Blue",
        "user": {
            "id": "u1",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    },
    {
        "vehicleNumber": "XYZ789",
        "vehicleType": "car",
        "make": "Honda",
        "model": "Civic",
        "color": "Red",
        "user": {
            "id": "u2",
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "555-5678",
        },
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    },
    {
        "vehicleNumber": "DEF456",
        "vehicleType": "suv",
        "make": "Ford",
        "model": "Explorer",
        "color": "Black",
        "user": {
            "id": "u3",
            "name": "Bob Johnson",
            "email": "bob@example.com",
            "phone": "555-9012",
        },
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
]

# Sample parking zones
SAMPLE_ZONES = [
    {
        "id": "z1",
        "name": "Downtown Parking",
        "address": "123 Main St, Downtown",
        "hourlyRate": 2.5,
        "totalSlots": 100,
        "availableSlots": 45
    },
    {
        "id": "z2",
        "name": "Mall Parking",
        "address": "456 Market Ave, Uptown",
        "hourlyRate": 3.0,
        "totalSlots": 200,
        "availableSlots": 20
    },
    {
        "id": "z3",
        "name": "Airport Parking",
        "address": "789 Airport Blvd, Terminal 1",
        "hourlyRate": 5.0,
        "totalSlots": 500,
        "availableSlots": 100
    }
]

# Sample active tickets (one for ABC123)
SAMPLE_TICKETS = [
    {
        "vehicleNumber": "ABC123",
        "zone": {
            "id": "z1",
            "name": "Downtown Parking",
            "hourlyRate": 2.5,
        },
        "slotNumber": "A12",
        "entryTime": datetime.utcnow() - timedelta(hours=2),  # 2 hours ago
        "status": "active",
        "createdAt": datetime.utcnow() - timedelta(hours=2),
        "updatedAt": datetime.utcnow() - timedelta(hours=2)
    }
]

def init_db():
    """Initialize the database with sample data"""
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(MONGODB_URI)
        db = client[MONGODB_DB]

        # Create collections if they don't exist
        if MONGODB_VEHICLES_COLLECTION not in db.list_collection_names():
            db.create_collection(MONGODB_VEHICLES_COLLECTION)

        if MONGODB_TICKETS_COLLECTION not in db.list_collection_names():
            db.create_collection(MONGODB_TICKETS_COLLECTION)

        # Get collection references
        vehicles_collection = db[MONGODB_VEHICLES_COLLECTION]
        tickets_collection = db[MONGODB_TICKETS_COLLECTION]

        # Create indexes
        vehicles_collection.create_index([("vehicleNumber", pymongo.ASCENDING)], unique=True)
        tickets_collection.create_index([("vehicleNumber", pymongo.ASCENDING), ("status", pymongo.ASCENDING)])

        # Check if collections are empty before inserting sample data
        if vehicles_collection.count_documents({}) == 0:
            # Insert sample vehicles
            vehicles_collection.insert_many(SAMPLE_VEHICLES)
            logger.info(f"Inserted {len(SAMPLE_VEHICLES)} sample vehicles")
        else:
            logger.info("Vehicles collection already has data, skipping sample data insertion")

        if tickets_collection.count_documents({}) == 0:
            # Insert sample tickets
            tickets_collection.insert_many(SAMPLE_TICKETS)
            logger.info(f"Inserted {len(SAMPLE_TICKETS)} sample tickets")
        else:
            logger.info("Tickets collection already has data, skipping sample data insertion")

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        # Close the connection
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    init_db()
