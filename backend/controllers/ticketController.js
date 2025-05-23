const Ticket = require('../models/Ticket');
const Vehicle = require('../models/Vehicle');
const Zone = require('../models/Zone');
const Notification = require('../models/Notification');

// @desc    Get all tickets
// @route   GET /api/tickets
// @access  Private/Admin
exports.getTickets = async (req, res) => {
  try {
    const tickets = await Ticket.find()
      .populate('user', 'name email')
      .populate('vehicle', 'vehicleNumber vehicleType')
      .populate('zone', 'name address hourlyRate');

    res.status(200).json({
      success: true,
      count: tickets.length,
      data: tickets,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get user tickets
// @route   GET /api/tickets/user
// @access  Private
exports.getUserTickets = async (req, res) => {
  try {
    const tickets = await Ticket.find({ user: req.user.id })
      .populate('vehicle', 'vehicleNumber vehicleType')
      .populate('zone', 'name address hourlyRate');

    res.status(200).json({
      success: true,
      count: tickets.length,
      data: tickets,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get zone tickets
// @route   GET /api/tickets/zone/:zoneId
// @access  Private/Operator
exports.getZoneTickets = async (req, res) => {
  try {
    // Check if operator owns the zone
    const zone = await Zone.findById(req.params.zoneId);

    if (!zone) {
      return res.status(404).json({
        success: false,
        message: `Zone not found with id of ${req.params.zoneId}`,
      });
    }

    if (zone.operator.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: 'Not authorized to access tickets for this zone',
      });
    }

    const tickets = await Ticket.find({ zone: req.params.zoneId })
      .populate('user', 'name email phone')
      .populate('vehicle', 'vehicleNumber vehicleType')
      .populate('zone', 'name address hourlyRate');

    res.status(200).json({
      success: true,
      count: tickets.length,
      data: tickets,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get single ticket
// @route   GET /api/tickets/:id
// @access  Private
exports.getTicket = async (req, res) => {
  try {
    const ticket = await Ticket.findById(req.params.id)
      .populate('user', 'name email phone')
      .populate('vehicle', 'vehicleNumber vehicleType')
      .populate('zone', 'name address hourlyRate');

    if (!ticket) {
      return res.status(404).json({
        success: false,
        message: `Ticket not found with id of ${req.params.id}`,
      });
    }

    // Make sure user owns ticket or is admin/operator of the zone
    if (
      ticket.user._id.toString() !== req.user.id &&
      req.user.role !== 'admin' &&
      (req.user.role === 'operator' &&
       ticket.zone.operator.toString() !== req.user.id)
    ) {
      return res.status(401).json({
        success: false,
        message: 'Not authorized to access this ticket',
      });
    }

    res.status(200).json({
      success: true,
      data: ticket,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Create ticket
// @route   POST /api/tickets
// @access  Private/Operator
exports.createTicket = async (req, res) => {
  try {
    const { vehicleId, zoneId, slotNumber, isReservation, reservationTime } = req.body;

    // Check if vehicle exists
    const vehicle = await Vehicle.findById(vehicleId).populate('user');
    if (!vehicle) {
      return res.status(404).json({
        success: false,
        message: `Vehicle not found with id of ${vehicleId}`,
      });
    }

    // Check if zone exists
    const zone = await Zone.findById(zoneId);
    if (!zone) {
      return res.status(404).json({
        success: false,
        message: `Zone not found with id of ${zoneId}`,
      });
    }

    // Check if zone is approved
    if (zone.status !== 'approved') {
      return res.status(400).json({
        success: false,
        message: 'Cannot create ticket for unapproved zone',
      });
    }

    // Check if operator owns the zone
    if (zone.operator.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: 'Not authorized to create tickets for this zone',
      });
    }

    // Check if zone has available slots
    if (zone.availableSlots <= 0) {
      return res.status(400).json({
        success: false,
        message: 'No available slots in this zone',
      });
    }

    // Create ticket
    const ticket = await Ticket.create({
      user: vehicle.user._id,
      vehicle: vehicleId,
      zone: zoneId,
      slotNumber,
      isReservation,
      reservationTime,
      hourlyRate: zone.hourlyRate, // Store hourly rate at time of ticket creation
    });

    // Update available slots in zone
    await Zone.findByIdAndUpdate(zoneId, {
      $inc: { availableSlots: -1 },
    });

    // Create notification for user
    await Notification.create({
      user: vehicle.user._id,
      title: isReservation ? 'Parking Reserved' : 'Parking Check-in',
      message: isReservation
        ? `Your parking has been reserved at ${zone.name} for ${new Date(
            reservationTime
          ).toLocaleString()}`
        : `Your vehicle ${vehicle.vehicleNumber} has been checked in at ${
            zone.name
          }`,
      type: isReservation ? 'reservation' : 'ticket',
      relatedTo: ticket._id,
      onModel: 'Ticket',
    });

    res.status(201).json({
      success: true,
      data: ticket,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Update ticket (checkout)
// @route   PUT /api/tickets/:id/checkout
// @access  Private/Operator
exports.checkoutTicket = async (req, res) => {
  try {
    const ticket = await Ticket.findById(req.params.id)
      .populate('zone')
      .populate('vehicle');

    if (!ticket) {
      return res.status(404).json({
        success: false,
        message: `Ticket not found with id of ${req.params.id}`,
      });
    }

    // Check if ticket is already completed
    if (ticket.status !== 'active') {
      return res.status(400).json({
        success: false,
        message: 'Ticket is not active',
      });
    }

    // Check if operator owns the zone
    if (
      ticket.zone.operator.toString() !== req.user.id &&
      req.user.role !== 'admin'
    ) {
      return res.status(401).json({
        success: false,
        message: 'Not authorized to checkout tickets for this zone',
      });
    }

    // Set exit time and calculate amount
    const exitTime = new Date();
    const entryTime = new Date(ticket.entryTime);
    const durationHours = (exitTime - entryTime) / (1000 * 60 * 60);
    const amount = durationHours * ticket.zone.hourlyRate;

    // Update ticket
    const updatedTicket = await Ticket.findByIdAndUpdate(
      req.params.id,
      {
        exitTime,
        status: 'completed',
        amount: parseFloat(amount.toFixed(2)),
      },
      {
        new: true,
        runValidators: true,
      }
    );

    // Update available slots in zone
    await Zone.findByIdAndUpdate(ticket.zone._id, {
      $inc: { availableSlots: 1 },
    });

    // Create notification for user
    await Notification.create({
      user: ticket.user,
      title: 'Parking Checkout',
      message: `Your vehicle ${ticket.vehicle.vehicleNumber} has been checked out. Amount: ₹${amount.toFixed(
        2
      )}`,
      type: 'payment',
      relatedTo: ticket._id,
      onModel: 'Ticket',
    });

    res.status(200).json({
      success: true,
      data: updatedTicket,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get active ticket by vehicle number
// @route   GET /api/tickets/vehicle/:vehicleNumber
// @access  Private/Operator
exports.getActiveTicketByVehicle = async (req, res) => {
  try {
    // Find vehicle by number
    const vehicle = await Vehicle.findOne({
      vehicleNumber: req.params.vehicleNumber,
    });

    if (!vehicle) {
      return res.status(404).json({
        success: false,
        message: `Vehicle not found with number ${req.params.vehicleNumber}`,
      });
    }

    // Find active ticket for vehicle
    const ticket = await Ticket.findOne({
      vehicle: vehicle._id,
      status: 'active',
    })
      .populate('user', 'name email phone')
      .populate('vehicle', 'vehicleNumber vehicleType')
      .populate('zone', 'name address hourlyRate');

    if (!ticket) {
      return res.status(404).json({
        success: false,
        message: `No active ticket found for vehicle ${req.params.vehicleNumber}`,
      });
    }

    // Check if operator owns the zone
    if (
      ticket.zone.operator.toString() !== req.user.id &&
      req.user.role !== 'admin'
    ) {
      return res.status(401).json({
        success: false,
        message: 'Not authorized to access tickets for this zone',
      });
    }

    res.status(200).json({
      success: true,
      data: ticket,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};
