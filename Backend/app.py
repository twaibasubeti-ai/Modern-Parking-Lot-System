
# =========================================================
# SMARTPARK
# Smart Parking Management System
# Backend Application
# =========================================================

# Flask is used to create the web application and API routes.
from flask import Flask, request, jsonify, send_from_directory

# SQLite is used as the database for storing parking information.
import sqlite3

# os is used for working with folders and file paths.
import os

# datetime is used to record vehicle entry and exit times.
from datetime import datetime

# math is used when calculating parking hours.
import math


# =========================================================
# CREATE FLASK APPLICATION
# =========================================================

# Create the Flask application.
app = Flask(__name__)


# =========================================================
# FOLDERS AND DATABASE
# =========================================================

# Find the main project folder.
# The backend folder is expected to be inside the main project folder.
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# Location where the database folder will be stored.
DATABASE_DIR = os.path.join(
    BASE_DIR,
    "Database"
)

# Full path to the SQLite database.
DATABASE_FILE = os.path.join(
    DATABASE_DIR,
    "parking.db"
)

# Location of the frontend folder.
FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "Frontend"
)


# =========================================================
# SMARTPARK SETTINGS
# =========================================================

# Total number of parking spaces in SmartPark.
TOTAL_SPACES = 20


# =========================================================
# VEHICLE TYPES AND PARKING RATES
# =========================================================

# Each vehicle category has its own hourly parking rate.
#
# These are example rates and can be changed later.
VEHICLE_RATES = {

    "Small Car": 100,

    "SUV / 4x4": 150,

    "Motorcycle": 50,

    "Van / Minibus": 200,

    "Truck": 300
}


# =========================================================
# PARKING ZONES
# =========================================================

# Each parking zone is assigned to a particular vehicle type.
#
# Example:
# Spaces 1-8 are for Small Cars.
# Spaces 9-12 are for SUVs / 4x4s.
#
# Format:
# (first space, last space, vehicle type)

PARKING_ZONES = [

    (1, 8, "Small Car"),

    (9, 12, "SUV / 4x4"),

    (13, 16, "Motorcycle"),

    (17, 18, "Van / Minibus"),

    (19, 20, "Truck")
]


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    # Make sure that the Database folder exists.
    os.makedirs(
        DATABASE_DIR,
        exist_ok=True
    )

    # Connect to the SQLite database.
    connection = sqlite3.connect(
        DATABASE_FILE
    )

    # Allow us to access database columns by name.
    # For example:
    # vehicle["plate_number"]
    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# ADD COLUMN TO EXISTING DATABASE
# =========================================================

def add_column_if_missing(
    connection,
    table_name,
    column_name,
    column_definition
):

    # Get information about the columns
    # that already exist in the table.
    cursor = connection.cursor()

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = [
        column["name"]
        for column in cursor.fetchall()
    ]

    # If the column does not exist,
    # add it to the table.
    if column_name not in columns:

        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name}
            {column_definition}
            """
        )


# =========================================================
# GET VEHICLE TYPE FOR A PARKING SPACE
# =========================================================

def get_space_vehicle_type(space_number):

    # Convert the space number to an integer.
    space_number = int(space_number)

    # Look through all parking zones.
    for start, end, vehicle_type in PARKING_ZONES:

        # Check whether the space belongs to this zone.
        if start <= space_number <= end:

            return vehicle_type

    # Default vehicle category.
    return "Small Car"


# =========================================================
# GENERATE TICKET NUMBER
# =========================================================

def generate_ticket_number(vehicle_id):

    # Every vehicle gets a unique SmartPark ticket number.
    #
    # Example:
    # Vehicle ID 1 -> SP-000001
    # Vehicle ID 25 -> SP-000025

    return f"SP-{int(vehicle_id):06d}"


# =========================================================
# CALCULATE PARKING FEE
# =========================================================

def calculate_fee(
    duration_minutes,
    vehicle_type
):

    # Get the hourly rate for the selected vehicle.
    #
    # If the vehicle type does not exist,
    # use the Small Car rate.
    rate = VEHICLE_RATES.get(
        vehicle_type,
        VEHICLE_RATES["Small Car"]
    )

    # Convert minutes into hours.
    #
    # We use math.ceil() so that any extra minutes
    # are charged as another hour.
    #
    # Examples:
    # 20 minutes  = 1 hour
    # 60 minutes  = 1 hour
    # 61 minutes  = 2 hours
    # 125 minutes = 3 hours

    hours = max(
        1,
        math.ceil(
            duration_minutes / 60
        )
    )

    # Calculate the total parking fee.
    total_fee = hours * rate

    return total_fee


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def initialize_database():

    # Connect to the database.
    connection = get_db_connection()

    cursor = connection.cursor()


    # =====================================================
    # PARKING SPACES TABLE
    # =====================================================

    # Create the parking_spaces table if it does not exist.
    #
    # Every parking space has:
    # - An ID
    # - Space number
    # - Vehicle category
    # - Current status

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_spaces (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            space_number INTEGER UNIQUE NOT NULL,

            vehicle_type TEXT DEFAULT 'Small Car',

            status TEXT NOT NULL

        )
    """)


    # =====================================================
    # VEHICLES TABLE
    # =====================================================

    # Create the vehicles table.
    #
    # This table stores information about every vehicle
    # that enters the parking lot.

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            ticket_number TEXT UNIQUE,

            driver_name TEXT,

            plate_number TEXT NOT NULL,

            vehicle_type TEXT DEFAULT 'Small Car',

            space_number INTEGER NOT NULL,

            entry_time TEXT NOT NULL,

            exit_time TEXT,

            duration_minutes INTEGER,

            amount_paid REAL DEFAULT 0,

            status TEXT NOT NULL

        )
    """)


    # =====================================================
    # PAYMENTS TABLE
    # =====================================================

    # Create the payments table.
    #
    # This stores information about payments
    # made when vehicles leave the parking lot.

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            vehicle_id INTEGER NOT NULL,

            amount REAL NOT NULL,

            payment_time TEXT NOT NULL,

            payment_status TEXT NOT NULL,

            payment_method TEXT

        )
    """)


    # =====================================================
    # DATABASE MIGRATION
    # =====================================================

    # The following commands allow the new system to work
    # with the old database you already created.
    #
    # They add new columns only if they don't already exist.


    # Add ticket number to old vehicle records.
    add_column_if_missing(
        connection,
        "vehicles",
        "ticket_number",
        "TEXT"
    )


    # Add driver's name.
    add_column_if_missing(
        connection,
        "vehicles",
        "driver_name",
        "TEXT"
    )


    # Add vehicle category.
    add_column_if_missing(
        connection,
        "vehicles",
        "vehicle_type",
        "TEXT DEFAULT 'Small Car'"
    )


    # Add vehicle category to old parking spaces.
    add_column_if_missing(
        connection,
        "parking_spaces",
        "vehicle_type",
        "TEXT DEFAULT 'Small Car'"
    )


    # =====================================================
    # CREATE PARKING SPACES
    # =====================================================

    # Create all 20 parking spaces.
    for space_number in range(
        1,
        TOTAL_SPACES + 1
    ):

        # Find which vehicle category
        # belongs to this parking space.
        vehicle_type = get_space_vehicle_type(
            space_number
        )

        # Insert the parking space if it does not exist.
        cursor.execute("""
            INSERT OR IGNORE INTO parking_spaces
            (
                space_number,
                vehicle_type,
                status
            )
            VALUES (?, ?, ?)
        """, (
            space_number,
            vehicle_type,
            "Available"
        ))


        # Make sure existing parking spaces
        # have the correct vehicle category.
        cursor.execute("""
            UPDATE parking_spaces

            SET vehicle_type = ?

            WHERE space_number = ?
        """, (
            vehicle_type,
            space_number
        ))


    # =====================================================
    # UPDATE OLD VEHICLES
    # =====================================================

    # Any old vehicle that does not have a category
    # will be classified as a Small Car.
    cursor.execute("""
        UPDATE vehicles

        SET vehicle_type = 'Small Car'

        WHERE vehicle_type IS NULL
        OR vehicle_type = ''
    """)


    # =====================================================
    # CREATE TICKET NUMBERS FOR OLD VEHICLES
    # =====================================================

    # Find old vehicles that don't have ticket numbers.
    old_vehicles = cursor.execute("""
        SELECT id

        FROM vehicles

        WHERE ticket_number IS NULL

        OR ticket_number = ''
    """).fetchall()


    # Give each old vehicle a SmartPark ticket number.
    for vehicle in old_vehicles:

        ticket_number = generate_ticket_number(
            vehicle["id"]
        )

        cursor.execute("""
            UPDATE vehicles

            SET ticket_number = ?

            WHERE id = ?
        """, (
            ticket_number,
            vehicle["id"]
        ))


    # Save all database changes.
    connection.commit()

    # Close the database connection.
    connection.close()


# =========================================================
# FRONTEND ROUTES
# =========================================================

# Send the main HTML page to the browser.
@app.route("/")
def home():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# Send the CSS file to the browser.
@app.route("/style.css")
def style():

    return send_from_directory(
        FRONTEND_DIR,
        "style.css"
    )


# Send the JavaScript file to the browser.
@app.route("/script.js")
def script():

    return send_from_directory(
        FRONTEND_DIR,
        "script.js"
    )


# =========================================================
# VEHICLE TYPES
# =========================================================

@app.route(
    "/vehicle-types",
    methods=["GET"]
)
def vehicle_types():

    # Create a list that will contain
    # all vehicle categories and their rates.
    vehicle_list = []


    # Go through every vehicle category.
    for vehicle_type, rate in VEHICLE_RATES.items():

        vehicle_list.append({

            "vehicle_type":
                vehicle_type,

            "hourly_rate":
                rate
        })


    # Send the vehicle categories to the frontend.
    return jsonify(
        vehicle_list
    )


# =========================================================
# GET ALL PARKING SPACES
# =========================================================

@app.route(
    "/parking-spaces",
    methods=["GET"]
)
def parking_spaces():

    # Open the database.
    connection = get_db_connection()


    # Retrieve every parking space.
    spaces = connection.execute("""
        SELECT *

        FROM parking_spaces

        ORDER BY space_number
    """).fetchall()


    # Close the database.
    connection.close()


    # Convert database rows into JSON.
    return jsonify([
        dict(space)
        for space in spaces
    ])


# =========================================================
# GET AVAILABLE PARKING SPACES
# =========================================================

@app.route(
    "/parking-spaces/available",
    methods=["GET"]
)
def available_spaces():

    # Get the vehicle type selected by the driver.
    vehicle_type = request.args.get(
        "vehicle_type"
    )


    # Connect to the database.
    connection = get_db_connection()


    # If a vehicle type was provided,
    # return only spaces suitable for that vehicle.
    if vehicle_type:

        spaces = connection.execute("""
            SELECT *

            FROM parking_spaces

            WHERE status = 'Available'

            AND vehicle_type = ?

            ORDER BY space_number
        """, (
            vehicle_type,
        )).fetchall()


    # Otherwise return all available spaces.
    else:

        spaces = connection.execute("""
            SELECT *

            FROM parking_spaces

            WHERE status = 'Available'

            ORDER BY space_number
        """).fetchall()


    # Close the connection.
    connection.close()


    # Return the spaces as JSON.
    return jsonify([
        dict(space)
        for space in spaces
    ])


# =========================================================
# VEHICLE ENTRY
# =========================================================

@app.route(
    "/vehicle/entry",
    methods=["POST"]
)
def vehicle_entry():

    # Receive information sent by JavaScript.
    data = request.get_json()


    # Make sure some data was submitted.
    if not data:

        return jsonify({
            "error":
                "No vehicle information was provided."
        }), 400


    # Get driver's name.
    driver_name = (
        data.get("driver_name")
        or ""
    ).strip()


    # Get plate number and convert it to uppercase.
    plate_number = (
        data.get("plate_number")
        or ""
    ).strip().upper()


    # Get selected vehicle category.
    vehicle_type = (
        data.get("vehicle_type")
        or ""
    ).strip()


    # Get selected parking space.
    space_number = data.get(
        "space_number"
    )


    # =====================================================
    # VALIDATE DRIVER NAME
    # =====================================================

    if not driver_name:

        return jsonify({
            "error":
                "Driver name is required."
        }), 400


    # =====================================================
    # VALIDATE PLATE NUMBER
    # =====================================================

    if not plate_number:

        return jsonify({
            "error":
                "Plate number is required."
        }), 400


    # =====================================================
    # VALIDATE VEHICLE TYPE
    # =====================================================

    if vehicle_type not in VEHICLE_RATES:

        return jsonify({
            "error":
                "Please select a valid vehicle type."
        }), 400


    # =====================================================
    # VALIDATE PARKING SPACE
    # =====================================================

    if not space_number:

        return jsonify({
            "error":
                "Please select a parking space."
        }), 400


    # Convert parking-space number to integer.
    try:

        space_number = int(
            space_number
        )

    except ValueError:

        return jsonify({
            "error":
                "Invalid parking space."
        }), 400


    # Open database connection.
    connection = get_db_connection()


    # =====================================================
    # CHECK THAT SPACE EXISTS
    # =====================================================

    space = connection.execute("""
        SELECT *

        FROM parking_spaces

        WHERE space_number = ?
    """, (
        space_number,
    )).fetchone()


    if not space:

        connection.close()

        return jsonify({
            "error":
                "Parking space does not exist."
        }), 404


    # =====================================================
    # CHECK VEHICLE TYPE AND SPACE TYPE
    # =====================================================

    # This prevents a motorcycle from being parked
    # in an SUV space, for example.

    if space["vehicle_type"] != vehicle_type:

        connection.close()

        return jsonify({
            "error":
                f"This space is reserved for "
                f"{space['vehicle_type']} vehicles."
        }), 400


    # =====================================================
    # CHECK SPACE AVAILABILITY
    # =====================================================

    if space["status"] != "Available":

        connection.close()

        return jsonify({
            "error":
                "Parking space is already occupied."
        }), 400


    # =====================================================
    # CHECK WHETHER VEHICLE IS ALREADY PARKED
    # =====================================================

    existing_vehicle = connection.execute("""
        SELECT *

        FROM vehicles

        WHERE plate_number = ?

        AND status = 'Parked'
    """, (
        plate_number,
    )).fetchone()


    if existing_vehicle:

        connection.close()

        return jsonify({
            "error":
                "This vehicle is already parked."
        }), 400


    # =====================================================
    # RECORD ENTRY TIME
    # =====================================================

    entry_time = datetime.now()


    # =====================================================
    # SAVE VEHICLE INFORMATION
    # =====================================================

    cursor = connection.execute("""
        INSERT INTO vehicles
        (
            driver_name,
            plate_number,
            vehicle_type,
            space_number,
            entry_time,
            status
        )

        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        driver_name,
        plate_number,
        vehicle_type,
        space_number,
        entry_time.isoformat(),
        "Parked"
    ))


    # Get the ID generated by SQLite.
    vehicle_id = cursor.lastrowid


    # =====================================================
    # GENERATE PARKING TICKET
    # =====================================================

    ticket_number = generate_ticket_number(
        vehicle_id
    )


    # Save the ticket number in the database.
    connection.execute("""
        UPDATE vehicles

        SET ticket_number = ?

        WHERE id = ?
    """, (
        ticket_number,
        vehicle_id
    ))


    # =====================================================
    # MARK PARKING SPACE AS OCCUPIED
    # =====================================================

    connection.execute("""
        UPDATE parking_spaces

        SET status = 'Occupied'

        WHERE space_number = ?
    """, (
        space_number,
    ))


    # Save all changes.
    connection.commit()

    # Close database connection.
    connection.close()


    # =====================================================
    # RETURN TICKET INFORMATION
    # =====================================================

    # This information will be used by JavaScript
    # to create the parking ticket on the screen.

    return jsonify({

        "message":
            "Vehicle successfully parked.",

        "vehicle_id":
            vehicle_id,

        "ticket_number":
            ticket_number,

        "driver_name":
            driver_name,

        "plate_number":
            plate_number,

        "vehicle_type":
            vehicle_type,

        "space_number":
            space_number,

        "entry_time":
            entry_time.isoformat(),

        "exit_time":
            None,

        "fee":
            0,

        "status":
            "Parked"

    }), 201


# =========================================================
# CURRENTLY PARKED VEHICLES
# =========================================================

@app.route(
    "/vehicles",
    methods=["GET"]
)
def vehicles():

    # Connect to database.
    connection = get_db_connection()


    # Get vehicles that are currently inside the parking lot.
    vehicles = connection.execute("""
        SELECT *

        FROM vehicles

        WHERE status = 'Parked'

        ORDER BY entry_time DESC
    """).fetchall()


    # Close connection.
    connection.close()


    # Convert results into JSON.
    return jsonify([
        dict(vehicle)
        for vehicle in vehicles
    ])


# =========================================================
# VEHICLE HISTORY
# =========================================================

@app.route(
    "/vehicle-history",
    methods=["GET"]
)
def vehicle_history():

    # Connect to database.
    connection = get_db_connection()


    # Retrieve vehicles that have already exited.
    #
    # LEFT JOIN is used to also retrieve their
    # payment information.

    vehicles = connection.execute("""
        SELECT

            v.*,

            p.payment_method,

            p.payment_time,

            p.payment_status

        FROM vehicles v

        LEFT JOIN payments p

        ON v.id = p.vehicle_id

        AND p.payment_status = 'Paid'

        WHERE v.status = 'Exited'

        ORDER BY v.exit_time DESC
    """).fetchall()


    # Close database connection.
    connection.close()


    # Return the history.
    return jsonify([
        dict(vehicle)
        for vehicle in vehicles
    ])


# =========================================================
# GET TICKET INFORMATION
# =========================================================

@app.route(
    "/ticket/<int:vehicle_id>",
    methods=["GET"]
)
def get_ticket(vehicle_id):

    # Connect to database.
    connection = get_db_connection()


    # Find the vehicle using its ID.
    vehicle = connection.execute("""
        SELECT *

        FROM vehicles

        WHERE id = ?
    """, (
        vehicle_id,
    )).fetchone()


    # If no vehicle was found, return an error.
    if not vehicle:

        connection.close()

        return jsonify({
            "error":
                "Ticket not found."
        }), 404


    # Find the latest payment associated
    # with this vehicle.
    payment = connection.execute("""
        SELECT *

        FROM payments

        WHERE vehicle_id = ?

        ORDER BY payment_time DESC

        LIMIT 1
    """, (
        vehicle_id,
    )).fetchone()


    # Close database connection.
    connection.close()


    # Convert vehicle data into a dictionary.
    ticket = dict(vehicle)


    # Add payment information to the ticket.
    if payment:

        ticket["payment_method"] = (
            payment["payment_method"]
        )

        ticket["payment_time"] = (
            payment["payment_time"]
        )

        ticket["payment_status"] = (
            payment["payment_status"]
        )

    else:

        ticket["payment_method"] = None

        ticket["payment_time"] = None

        ticket["payment_status"] = "Pending"


    # Return ticket information.
    return jsonify(ticket)


# =========================================================
# VEHICLE EXIT
# =========================================================

@app.route(
    "/vehicle/exit/<int:vehicle_id>",
    methods=["POST"]
)
def vehicle_exit(vehicle_id):

    # Connect to database.
    connection = get_db_connection()


    # Find the currently parked vehicle.
    vehicle = connection.execute("""
        SELECT *

        FROM vehicles

        WHERE id = ?

        AND status = 'Parked'
    """, (
        vehicle_id,
    )).fetchone()


    # If vehicle doesn't exist or already exited.
    if not vehicle:

        connection.close()

        return jsonify({
            "error":
                "Vehicle is not currently parked."
        }), 404


    # Convert stored entry time back into a datetime object.
    entry_time = datetime.fromisoformat(
        vehicle["entry_time"]
    )


    # Record the current time as the exit time.
    exit_time = datetime.now()


    # Calculate how many seconds the vehicle stayed.
    duration_seconds = (
        exit_time - entry_time
    ).total_seconds()


    # Convert seconds into minutes.
    #
    # At least one minute is recorded.
    duration_minutes = max(
        1,
        int(duration_seconds / 60)
    )


    # Calculate the fee using the vehicle category.
    amount = calculate_fee(
        duration_minutes,
        vehicle["vehicle_type"]
    )


    # =====================================================
    # SAVE EXIT INFORMATION
    # =====================================================

    # The vehicle remains "Parked" until payment
    # has successfully been completed.

    connection.execute("""
        UPDATE vehicles

        SET

            exit_time = ?,

            duration_minutes = ?,

            amount_paid = ?

        WHERE id = ?
    """, (
        exit_time.isoformat(),
        duration_minutes,
        amount,
        vehicle_id
    ))


    # Save changes.
    connection.commit()

    # Close connection.
    connection.close()


    # Return information required by the payment modal
    # and final ticket.

    return jsonify({

        "vehicle_id":
            vehicle_id,

        "ticket_number":
            vehicle["ticket_number"],

        "driver_name":
            vehicle["driver_name"],

        "plate_number":
            vehicle["plate_number"],

        "vehicle_type":
            vehicle["vehicle_type"],

        "space_number":
            vehicle["space_number"],

        "entry_time":
            vehicle["entry_time"],

        "exit_time":
            exit_time.isoformat(),

        "duration_minutes":
            duration_minutes,

        "amount":
            amount

    })


# =========================================================
# PAYMENT
# =========================================================

@app.route(
    "/payment/<int:vehicle_id>",
    methods=["POST"]
)
def payment(vehicle_id):

    # Receive payment information from the frontend.
    data = request.get_json()


    # Get the selected payment method.
    payment_method = (
        data.get("payment_method")
        if data
        else None
    )


    # Make sure a payment method was selected.
    if not payment_method:

        return jsonify({
            "error":
                "Payment method is required."
        }), 400


    # List of payment methods supported by SmartPark.
    valid_methods = [
        "mpesa",
        "cash",
        "card"
    ]


    # Check whether the selected method is valid.
    if payment_method not in valid_methods:

        return jsonify({
            "error":
                "Invalid payment method."
        }), 400


    # Connect to database.
    connection = get_db_connection()


    # Find the vehicle.
    vehicle = connection.execute("""
        SELECT *

        FROM vehicles

        WHERE id = ?

        AND status = 'Parked'
    """, (
        vehicle_id,
    )).fetchone()


    # Make sure the vehicle exists.
    if not vehicle:

        connection.close()

        return jsonify({
            "error":
                "Vehicle not found or payment has already been completed."
        }), 404


    # =====================================================
    # MAKE SURE EXIT INFORMATION EXISTS
    # =====================================================

    if not vehicle["exit_time"]:

        connection.close()

        return jsonify({
            "error":
                "Vehicle exit must be calculated before payment."
        }), 400


    # =====================================================
    # CALCULATE FINAL FEE
    # =====================================================

    # The server calculates the final fee itself.
    # This prevents the frontend from changing
    # the amount being paid.

    amount = calculate_fee(
        vehicle["duration_minutes"],
        vehicle["vehicle_type"]
    )


    # Record payment time.
    payment_time = datetime.now()


    # =====================================================
    # SAVE PAYMENT
    # =====================================================

    connection.execute("""
        INSERT INTO payments
        (
            vehicle_id,
            amount,
            payment_time,
            payment_status,
            payment_method
        )

        VALUES (?, ?, ?, ?, ?)
    """, (
        vehicle_id,
        amount,
        payment_time.isoformat(),
        "Paid",
        payment_method
    ))


    # =====================================================
    # MARK VEHICLE AS EXITED
    # =====================================================

    connection.execute("""
        UPDATE vehicles

        SET

            status = 'Exited',

            amount_paid = ?

        WHERE id = ?
    """, (
        amount,
        vehicle_id
    ))


    # =====================================================
    # FREE PARKING SPACE
    # =====================================================

    # Once payment is completed,
    # the vehicle leaves and its space becomes available.

    connection.execute("""
        UPDATE parking_spaces

        SET status = 'Available'

        WHERE space_number = ?
    """, (
        vehicle["space_number"],
    ))


    # Save all changes.
    connection.commit()

    # Close database connection.
    connection.close()


    # Return payment result.
    return jsonify({

        "message":
            "Payment successful.",

        "vehicle_id":
            vehicle_id,

        "ticket_number":
            vehicle["ticket_number"],

        "amount":
            amount,

        "payment_method":
            payment_method,

        "payment_status":
            "Paid",

        # The system can use this to represent
        # that the parking barrier can now open.
        "barrier":
            "OPEN"

    })


# =========================================================
# BARRIER STATUS
# =========================================================

@app.route(
    "/barrier/<int:vehicle_id>",
    methods=["GET"]
)
def barrier(vehicle_id):

    # Connect to database.
    connection = get_db_connection()


    # Check whether the vehicle has a successful payment.
    payment = connection.execute("""
        SELECT *

        FROM payments

        WHERE vehicle_id = ?

        AND payment_status = 'Paid'

        ORDER BY payment_time DESC

        LIMIT 1
    """, (
        vehicle_id,
    )).fetchone()


    # Close database.
    connection.close()


    # If payment exists, the barrier can open.
    if payment:

        return jsonify({
            "barrier": "OPEN"
        })


    # Otherwise the barrier remains closed.
    return jsonify({
        "barrier": "CLOSED"
    })


# =========================================================
# DASHBOARD STATISTICS
# =========================================================

@app.route(
    "/statistics",
    methods=["GET"]
)
def statistics():

    # Connect to database.
    connection = get_db_connection()


    # Count all parking spaces.
    total_spaces = connection.execute("""
        SELECT COUNT(*)

        FROM parking_spaces
    """).fetchone()[0]


    # Count occupied spaces.
    occupied_spaces = connection.execute("""
        SELECT COUNT(*)

        FROM parking_spaces

        WHERE status = 'Occupied'
    """).fetchone()[0]


    # Calculate available spaces.
    available_spaces = (
        total_spaces
        - occupied_spaces
    )


    # Count vehicles currently parked.
    parked_vehicles = connection.execute("""
        SELECT COUNT(*)

        FROM vehicles

        WHERE status = 'Parked'
    """).fetchone()[0]


    # Calculate total revenue from successful payments.
    total_revenue = connection.execute("""
        SELECT COALESCE(
            SUM(amount),
            0
        )

        FROM payments

        WHERE payment_status = 'Paid'
    """).fetchone()[0]


    # =====================================================
    # COUNT PARKED VEHICLES BY CATEGORY
    # =====================================================

    category_counts = connection.execute("""
        SELECT

            vehicle_type,

            COUNT(*) AS total

        FROM vehicles

        WHERE status = 'Parked'

        GROUP BY vehicle_type
    """).fetchall()


    # Close database.
    connection.close()


    # Convert category results into a dictionary.
    vehicles_by_type = {

        row["vehicle_type"]:
        row["total"]

        for row in category_counts
    }


    # Return all dashboard statistics.
    return jsonify({

        "total_spaces":
            total_spaces,

        "occupied_spaces":
            occupied_spaces,

        "available_spaces":
            available_spaces,

        "parked_vehicles":
            parked_vehicles,

        "total_revenue":
            total_revenue,

        "vehicles_by_type":
            vehicles_by_type

    })


# =========================================================
# START SMARTPARK SERVER
# =========================================================

if __name__ == "__main__":

    # Create the database and required tables
    # before starting the server.
    initialize_database()


    # Display useful information in the terminal.
    print()
    print("=" * 55)
    print("                 SMARTPARK")
    print("       Smart Parking Management System")
    print("=" * 55)
    print()
    print("Total parking spaces: 20")
    print("Server: http://127.0.0.1:5000")
    print()
    print("=" * 55)


    # Start the Flask development server.
    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000
    )

