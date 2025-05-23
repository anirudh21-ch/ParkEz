import requests
import json
import sys
import os
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:5002/api"  # Backend API URL
OPERATOR_EMAIL = "testoperator@parkez.com"  # New operator account
OPERATOR_PASSWORD = "password123"  # Password we just set
VEHICLE_NUMBER = "ABC123"  # One of the sample vehicles
ZONE_ID = None  # Will be set after login
SLOT_NUMBER = "A12"

def login_operator():
    """Login as operator and get auth token"""
    print("Logging in as operator...")

    response = requests.post(f"{API_URL}/auth/login", json={
        "email": OPERATOR_EMAIL,
        "password": OPERATOR_PASSWORD
    })

    if response.status_code != 200:
        print(f"Error logging in: {response.status_code}")
        print(response.text)
        sys.exit(1)

    data = response.json()
    if not data.get("success"):
        print(f"Login failed: {data.get('message')}")
        sys.exit(1)

    token = data.get("token")
    user = data.get("user")

    print(f"Logged in as {user.get('name')} (Role: {user.get('role')})")
    return token

def get_zones(token):
    """Get available parking zones"""
    print("\nFetching available zones...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/zones", headers=headers)

    if response.status_code != 200:
        print(f"Error fetching zones: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    if not data.get("success"):
        print(f"Failed to fetch zones: {data.get('message')}")
        return None

    zones = data.get("data", [])
    if not zones:
        print("No zones available")
        return None

    print(f"Found {len(zones)} zones:")
    for i, zone in enumerate(zones):
        print(f"{i+1}. {zone.get('name')} - {zone.get('availableSlots')} slots available - ${zone.get('hourlyRate')}/hr")

    # Return the first zone for simplicity
    return zones[0]

def get_vehicle_by_number(token, vehicle_number):
    """Get vehicle details by license plate number"""
    print(f"\nLooking up vehicle with license plate: {vehicle_number}")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/vehicles/number/{vehicle_number}", headers=headers)

    if response.status_code != 200:
        print(f"Error fetching vehicle: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    if not data.get("success"):
        print(f"Failed to fetch vehicle: {data.get('message')}")
        return None

    vehicle = data.get("data")
    print(f"Found vehicle: {vehicle.get('vehicleNumber')} - {vehicle.get('make')} {vehicle.get('model')} ({vehicle.get('color')})")
    return vehicle

def get_active_ticket(token, vehicle_number):
    """Check if vehicle has an active ticket"""
    print(f"\nChecking for active tickets for vehicle: {vehicle_number}")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/tickets/vehicle/{vehicle_number}", headers=headers)

    if response.status_code != 200:
        print(f"Error checking active ticket: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    if not data.get("success"):
        print(f"Failed to check active ticket: {data.get('message')}")
        return None

    ticket = data.get("data")
    if ticket:
        print(f"Active ticket found: {ticket.get('_id')} - Zone: {ticket.get('zone', {}).get('name')} - Slot: {ticket.get('slotNumber')}")
    else:
        print("No active ticket found")

    return ticket

def create_ticket(token, vehicle_id, zone_id, slot_number):
    """Create a new parking ticket (entry)"""
    print(f"\nCreating ticket for vehicle {vehicle_id} in zone {zone_id}, slot {slot_number}...")

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "vehicleId": vehicle_id,
        "zoneId": zone_id,
        "slotNumber": slot_number
    }

    response = requests.post(f"{API_URL}/tickets", json=payload, headers=headers)

    if response.status_code != 201:
        print(f"Error creating ticket: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    if not data.get("success"):
        print(f"Failed to create ticket: {data.get('message')}")
        return None

    ticket = data.get("data")
    print(f"Ticket created successfully: {ticket.get('_id')}")
    print(f"Entry time: {ticket.get('entryTime')}")
    print(f"Hourly rate: ${ticket.get('hourlyRate')}/hr")

    return ticket

def checkout_ticket(token, ticket_id):
    """Checkout a ticket (exit)"""
    print(f"\nChecking out ticket: {ticket_id}...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(f"{API_URL}/tickets/{ticket_id}/checkout", headers=headers)

    if response.status_code != 200:
        print(f"Error checking out ticket: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    if not data.get("success"):
        print(f"Failed to checkout ticket: {data.get('message')}")
        return None

    ticket = data.get("data")

    # Calculate duration
    entry_time = datetime.fromisoformat(ticket.get('entryTime').replace('Z', '+00:00'))
    exit_time = datetime.fromisoformat(ticket.get('exitTime').replace('Z', '+00:00'))
    duration_seconds = (exit_time - entry_time).total_seconds()
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)

    print(f"Ticket checked out successfully")
    print(f"Entry time: {entry_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Exit time: {exit_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {hours} hours, {minutes} minutes")
    print(f"Amount: ${ticket.get('amount')}")

    return ticket

def simulate_entry_flow():
    """Simulate the entry flow"""
    print("\n=== SIMULATING ENTRY FLOW ===\n")

    # Login as operator
    token = login_operator()

    # Get available zones
    zone = get_zones(token)
    if not zone:
        return

    # Get vehicle by license plate
    vehicle = get_vehicle_by_number(token, VEHICLE_NUMBER)
    if not vehicle:
        return

    # Check if vehicle has an active ticket
    active_ticket = get_active_ticket(token, VEHICLE_NUMBER)
    if active_ticket:
        print("Vehicle already has an active ticket. Cannot create a new one.")
        return

    # Create a new ticket
    ticket = create_ticket(token, vehicle.get('_id'), zone.get('_id'), SLOT_NUMBER)
    if not ticket:
        return

    print("\nEntry flow completed successfully!")
    return ticket

def simulate_exit_flow():
    """Simulate the exit flow"""
    print("\n=== SIMULATING EXIT FLOW ===\n")

    # Login as operator
    token = login_operator()

    # Get vehicle by license plate
    vehicle = get_vehicle_by_number(token, VEHICLE_NUMBER)
    if not vehicle:
        return

    # Check if vehicle has an active ticket
    active_ticket = get_active_ticket(token, VEHICLE_NUMBER)
    if not active_ticket:
        print("Vehicle does not have an active ticket. Cannot checkout.")
        return

    # Checkout the ticket
    checkout_ticket(token, active_ticket.get('_id'))

    print("\nExit flow completed successfully!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "exit":
        simulate_exit_flow()
    else:
        simulate_entry_flow()
