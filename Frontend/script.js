// =========================================================
// SMARTPARK
// Frontend JavaScript
// =========================================================


// =========================================================
// LOAD DASHBOARD STATISTICS
// =========================================================

async function loadStatistics() {
    try {
        const response = await fetch("/statistics");
        const data = await response.json();

        document.getElementById("totalSpaces").textContent =
            data.total_spaces;

        document.getElementById("availableSpaces").textContent =
            data.available_spaces;

        document.getElementById("occupiedSpaces").textContent =
            data.occupied_spaces;

        document.getElementById("totalRevenue").textContent =
            "KES " + Number(data.total_revenue).toLocaleString();

    } catch (error) {
        console.error("Error loading statistics:", error);
    }
}


// =========================================================
// LOAD PARKING SPACES
// GROUPED BY VEHICLE TYPE
// =========================================================

async function loadParkingSpaces() {

    try {

        const response = await fetch("/parking-spaces");

        const spaces = await response.json();

        const parkingGrid =
            document.getElementById("parkingGrid");

        if (!parkingGrid) {
            return;
        }

        // Clear old parking spaces
        parkingGrid.innerHTML = "";

        // Make the main container stack categories vertically
        parkingGrid.style.display = "flex";
        parkingGrid.style.flexDirection = "column";
        parkingGrid.style.gap = "30px";


        // =====================================================
        // VEHICLE CATEGORIES
        // =====================================================

        const vehicleGroups = {

            "Small Car": "🚗 Small Cars",

            "SUV / 4x4": "🚙 SUVs / 4x4",

            "Motorcycle": "🏍️ Motorcycles",

            "Van / Minibus": "🚐 Vans / Minibuses",

            "Truck": "🚛 Trucks"

        };


        // =====================================================
        // CREATE EACH VEHICLE CATEGORY
        // =====================================================

        Object.keys(vehicleGroups).forEach(function(vehicleType) {

            // Create category container
            const category =
                document.createElement("div");

            category.classList.add(
                "parking-category"
            );

            // Make sure each category takes the full width
            category.style.width = "100%";


            // -------------------------------------------------
            // CATEGORY HEADING
            // -------------------------------------------------

            const heading =
                document.createElement("h3");

            heading.classList.add(
                "parking-category-title"
            );

            heading.textContent =
                vehicleGroups[vehicleType];

            heading.style.marginBottom = "15px";


            // -------------------------------------------------
            // CREATE GRID FOR THIS CATEGORY
            // -------------------------------------------------

            const categoryGrid =
                document.createElement("div");

            categoryGrid.classList.add(
                "parking-grid"
            );


            // -------------------------------------------------
            // GET ONLY THE SPACES FOR THIS VEHICLE TYPE
            // -------------------------------------------------

            const categorySpaces =
                spaces.filter(function(space) {

                    return space.vehicle_type === vehicleType;

                });


            // =================================================
            // CREATE PARKING SLOT
            // =================================================

            categorySpaces.forEach(function(space) {

                const slot =
                    document.createElement("div");

                slot.classList.add(
                    "parking-slot"
                );


                // ------------------------------------------------
                // AVAILABLE SLOT
                // ------------------------------------------------

                if (space.status === "Available") {

                    slot.classList.add(
                        "available"
                    );

                    slot.innerHTML = `

                        <strong>
                            Slot ${space.space_number}
                        </strong>

                        <span>
                            Available
                        </span>

                        <span>
                            ${space.vehicle_type}
                        </span>

                    `;

                }


                // ------------------------------------------------
                // OCCUPIED SLOT
                // ------------------------------------------------

                else {

                    slot.classList.add(
                        "occupied"
                    );

                    slot.innerHTML = `

                        <strong>
                            Slot ${space.space_number}
                        </strong>

                        <span>
                            Occupied
                        </span>

                        <span>
                            ${space.vehicle_type}
                        </span>

                    `;

                }


                // Add slot to category grid
                categoryGrid.appendChild(slot);

            });


            // =================================================
            // ADD HEADING + GRID TO CATEGORY
            // =================================================

            category.appendChild(heading);

            category.appendChild(categoryGrid);

            parkingGrid.appendChild(category);

        });


    } catch (error) {

        console.error(
            "Error loading parking spaces:",
            error
        );

    }

}


// =========================================================
// LOAD AVAILABLE SPACES FOR SELECTED VEHICLE
// =========================================================

async function loadAvailableSpaces(vehicleType) {

    const spaceSelect =
        document.getElementById("spaceNumber");

    if (!spaceSelect) {
        return;
    }

    spaceSelect.innerHTML =
        '<option value="">Select parking space</option>';

    if (!vehicleType) {
        return;
    }

    try {

        const response =
            await fetch(
                `/parking-spaces/available?vehicle_type=${encodeURIComponent(vehicleType)}`
            );

        const spaces =
            await response.json();


        if (spaces.length === 0) {

            spaceSelect.innerHTML =
                '<option value="">No available spaces</option>';

            return;
        }


        spaces.forEach(function(space) {

            const option =
                document.createElement("option");

            option.value =
                space.space_number;

            option.textContent =
                `Slot ${space.space_number}`;

            spaceSelect.appendChild(option);

        });

    } catch (error) {

        console.error(
            "Error loading available spaces:",
            error
        );

    }

}


// =========================================================
// RECORD VEHICLE ENTRY
// =========================================================

async function recordVehicleEntry(event) {

    event.preventDefault();

    const driverName =
        document.getElementById("driverName").value.trim();

    const vehicleType =
        document.getElementById("vehicleType").value;

    const plateNumber =
        document.getElementById("plateNumber").value.trim();

    const spaceNumber =
        document.getElementById("spaceNumber").value;

    const message =
        document.getElementById("entryMessage");


    try {

        const response =
            await fetch("/vehicle/entry", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    driver_name:
                        driverName,

                    vehicle_type:
                        vehicleType,

                    plate_number:
                        plateNumber,

                    space_number:
                        spaceNumber

                })

            });


        const data =
            await response.json();


        if (!response.ok) {

            message.textContent =
                data.error || "Something went wrong.";

            message.className =
                "message error";

            return;
        }


        message.textContent =
            `Vehicle parked successfully. Ticket: ${data.ticket_number}`;

        message.className =
            "message success";


        document.getElementById(
            "entryForm"
        ).reset();


        document.getElementById(
            "spaceNumber"
        ).innerHTML =
            '<option value="">Select parking space</option>';


        // Refresh everything
        loadStatistics();
        loadParkingSpaces();
        loadVehicles();


        // Show ticket
        showTicket(data.vehicle_id);


    } catch (error) {

        console.error(
            "Error recording vehicle:",
            error
        );

        message.textContent =
            "Unable to connect to the server.";

        message.className =
            "message error";

    }

}


// =========================================================
// LOAD PARKED VEHICLES
// =========================================================

async function loadVehicles() {

    try {

        const response =
            await fetch("/vehicles");

        const vehicles =
            await response.json();

        const table =
            document.getElementById("vehicleTable");

        if (!table) {
            return;
        }

        table.innerHTML = "";


        if (vehicles.length === 0) {

            table.innerHTML = `

                <tr>
                    <td colspan="8">
                        No vehicles are currently parked.
                    </td>
                </tr>

            `;

            return;
        }


        vehicles.forEach(function(vehicle) {

            const row =
                document.createElement("tr");


            row.innerHTML = `

                <td>
                    ${vehicle.ticket_number || "-"}
                </td>

                <td>
                    ${vehicle.driver_name || "-"}
                </td>

                <td>
                    ${vehicle.plate_number}
                </td>

                <td>
                    ${vehicle.vehicle_type}
                </td>

                <td>
                    Slot ${vehicle.space_number}
                </td>

                <td>
                    ${formatDateTime(vehicle.entry_time)}
                </td>

                <td>
                    <span class="status-badge parked">
                        Parked
                    </span>
                </td>

                <td>

                    <button
                        class="btn-small"
                        onclick="vehicleExit(${vehicle.id})"
                    >
                        Exit
                    </button>

                    <button
                        class="btn-small"
                        onclick="showTicket(${vehicle.id})"
                    >
                        Ticket
                    </button>

                </td>

            `;


            table.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Error loading vehicles:",
            error
        );

    }

}


// =========================================================
// VEHICLE EXIT
// =========================================================

async function vehicleExit(vehicleId) {

    try {

        const response =
            await fetch(
                `/vehicle/exit/${vehicleId}`,
                {
                    method: "POST"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            alert(
                data.error ||
                "Unable to process vehicle exit."
            );

            return;
        }


        // Open payment modal
        openPaymentModal(data);


    } catch (error) {

        console.error(
            "Error processing vehicle exit:",
            error
        );

        alert(
            "Unable to connect to the server."
        );

    }

}


// =========================================================
// OPEN PAYMENT MODAL
// =========================================================

function openPaymentModal(vehicle) {

    document.getElementById(
        "paymentModal"
    ).style.display = "flex";


    document.getElementById(
        "paymentPlate"
    ).textContent =
        vehicle.plate_number;


    document.getElementById(
        "paymentDuration"
    ).textContent =
        vehicle.duration_minutes + " minutes";


    document.getElementById(
        "paymentAmount"
    ).textContent =
        "KES " +
        Number(vehicle.amount).toLocaleString();


    document.getElementById(
        "paymentModal"
    ).dataset.vehicleId =
        vehicle.vehicle_id;


    document.getElementById(
        "paymentMessage"
    ).textContent = "";


    showPaymentFields();

}


// =========================================================
// CLOSE PAYMENT MODAL
// =========================================================

function closePaymentModal() {

    document.getElementById(
        "paymentModal"
    ).style.display = "none";

}


// =========================================================
// SHOW PAYMENT FIELDS
// =========================================================

function showPaymentFields() {

    const method =
        document.getElementById(
            "paymentMethod"
        ).value;


    const mpesaFields =
        document.getElementById(
            "mpesaFields"
        );

    const cardFields =
        document.getElementById(
            "cardFields"
        );


    mpesaFields.style.display =
        method === "mpesa"
            ? "block"
            : "none";


    cardFields.style.display =
        method === "card"
            ? "block"
            : "none";

}


// =========================================================
// MAKE PAYMENT
// =========================================================

async function makePayment() {

    const modal =
        document.getElementById(
            "paymentModal"
        );


    const vehicleId =
        modal.dataset.vehicleId;


    const paymentMethod =
        document.getElementById(
            "paymentMethod"
        ).value;


    const message =
        document.getElementById(
            "paymentMessage"
        );


    if (!paymentMethod) {

        message.textContent =
            "Please select a payment method.";

        return;
    }


    try {

        const response =
            await fetch(
                `/payment/${vehicleId}`,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        payment_method:
                            paymentMethod

                    })

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            message.textContent =
                data.error ||
                "Payment failed.";

            return;
        }


        message.textContent =
            "Payment successful. Barrier OPEN.";


        setTimeout(function() {

            closePaymentModal();

            loadStatistics();

            loadParkingSpaces();

            loadVehicles();

            loadVehicleHistory();

        }, 1000);


    } catch (error) {

        console.error(
            "Payment error:",
            error
        );

        message.textContent =
            "Unable to process payment.";

    }

}


// =========================================================
// LOAD VEHICLE HISTORY
// =========================================================

async function loadVehicleHistory() {

    try {

        const response =
            await fetch(
                "/vehicle-history"
            );


        const vehicles =
            await response.json();


        const table =
            document.getElementById(
                "historyTable"
            );


        if (!table) {
            return;
        }


        table.innerHTML = "";


        if (vehicles.length === 0) {

            table.innerHTML = `

                <tr>

                    <td colspan="9">
                        No completed parking records yet.
                    </td>

                </tr>

            `;

            return;
        }


        vehicles.forEach(function(vehicle) {

            const row =
                document.createElement("tr");


            row.innerHTML = `

                <td>
                    ${vehicle.ticket_number || "-"}
                </td>

                <td>
                    ${vehicle.driver_name || "-"}
                </td>

                <td>
                    ${vehicle.plate_number}
                </td>

                <td>
                    ${vehicle.vehicle_type}
                </td>

                <td>
                    Slot ${vehicle.space_number}
                </td>

                <td>
                    ${formatDateTime(vehicle.entry_time)}
                </td>

                <td>
                    ${formatDateTime(vehicle.exit_time)}
                </td>

                <td>
                    KES ${Number(
                        vehicle.amount_paid || 0
                    ).toLocaleString()}
                </td>

                <td>

                    <button
                        class="btn-small"
                        onclick="loadCompletedTicket(${vehicle.id})"
                    >
                        View Ticket
                    </button>

                </td>

            `;


            table.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Error loading history:",
            error
        );

    }

}


// =========================================================
// SHOW TICKET
// =========================================================

async function showTicket(vehicleId) {

    try {

        const response =
            await fetch(
                `/ticket/${vehicleId}`
            );


        const ticket =
            await response.json();


        if (!response.ok) {

            alert(
                ticket.error ||
                "Ticket not found."
            );

            return;
        }


        document.getElementById(
            "ticketNumber"
        ).textContent =
            ticket.ticket_number || "-";


        document.getElementById(
            "ticketDriver"
        ).textContent =
            ticket.driver_name || "-";


        document.getElementById(
            "ticketPlate"
        ).textContent =
            ticket.plate_number || "-";


        document.getElementById(
            "ticketVehicleType"
        ).textContent =
            ticket.vehicle_type || "-";


        document.getElementById(
            "ticketSpace"
        ).textContent =
            "Slot " +
            (ticket.space_number || "-");


        document.getElementById(
            "ticketTimeIn"
        ).textContent =
            formatDateTime(
                ticket.entry_time
            );


        document.getElementById(
            "ticketTimeOut"
        ).textContent =
            ticket.exit_time
                ? formatDateTime(
                    ticket.exit_time
                )
                : "Not exited";


        document.getElementById(
            "ticketDuration"
        ).textContent =
            ticket.duration_minutes
                ? ticket.duration_minutes +
                  " minutes"
                : "Currently parked";


        document.getElementById(
            "ticketFee"
        ).textContent =
            "KES " +
            Number(
                ticket.amount_paid || 0
            ).toLocaleString();


        document.getElementById(
            "ticketPaymentMethod"
        ).textContent =
            ticket.payment_method
                ? ticket.payment_method.toUpperCase()
                : "Pending";


        document.getElementById(
            "ticketModal"
        ).style.display =
            "flex";


    } catch (error) {

        console.error(
            "Error loading ticket:",
            error
        );

    }

}


// =========================================================
// LOAD COMPLETED TICKET
// =========================================================

function loadCompletedTicket(vehicleId) {

    showTicket(vehicleId);

}


// =========================================================
// CLOSE TICKET MODAL
// =========================================================

function closeTicketModal() {

    document.getElementById(
        "ticketModal"
    ).style.display = "none";

}


// =========================================================
// PRINT TICKET
// =========================================================

function printTicket() {

    window.print();

}


// =========================================================
// FORMAT DATE AND TIME
// =========================================================

function formatDateTime(dateString) {

    if (!dateString) {
        return "-";
    }


    const date =
        new Date(dateString);


    return date.toLocaleString(
        "en-KE",
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    );

}


// =========================================================
// CLOSE MODALS WHEN CLICKING OUTSIDE
// =========================================================

window.addEventListener(
    "click",
    function(event) {

        const paymentModal =
            document.getElementById(
                "paymentModal"
            );

        const ticketModal =
            document.getElementById(
                "ticketModal"
            );


        if (
            event.target === paymentModal
        ) {

            closePaymentModal();

        }


        if (
            event.target === ticketModal
        ) {

            closeTicketModal();

        }

    }
);


// =========================================================
// LOAD DATA WHEN PAGE OPENS
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        loadStatistics();

        loadParkingSpaces();

        loadVehicles();

        loadVehicleHistory();

    }
);
