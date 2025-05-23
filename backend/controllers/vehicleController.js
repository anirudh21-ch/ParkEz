const Vehicle = require('../models/Vehicle');

// @desc    Get all vehicles
// @route   GET /api/vehicles
// @access  Private/Admin
exports.getVehicles = async (req, res) => {
  try {
    const vehicles = await Vehicle.find().populate('user', 'name email');

    res.status(200).json({
      success: true,
      count: vehicles.length,
      data: vehicles,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get user vehicles
// @route   GET /api/vehicles/user
// @access  Private
exports.getUserVehicles = async (req, res) => {
  try {
    const vehicles = await Vehicle.find({ user: req.user.id });

    res.status(200).json({
      success: true,
      count: vehicles.length,
      data: vehicles,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get single vehicle
// @route   GET /api/vehicles/:id
// @access  Private
exports.getVehicle = async (req, res) => {
  try {
    const vehicle = await Vehicle.findById(req.params.id).populate(
      'user',
      'name email'
    );

    if (!vehicle) {
      return res.status(404).json({
        success: false,
        message: `Vehicle not found with id of ${req.params.id}`,
      });
    }

    // Make sure user owns vehicle or is admin
    if (
      vehicle.user.toString() !== req.user.id &&
      req.user.role !== 'admin' &&
      req.user.role !== 'operator'
    ) {
      return res.status(401).json({
        success: false,
        message: `User ${req.user.id} is not authorized to access this vehicle`,
      });
    }

    res.status(200).json({
      success: true,
      data: vehicle,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Create vehicle
// @route   POST /api/vehicles
// @access  Private
exports.createVehicle = async (req, res) => {
  try {
    // Add user to req.body
    req.body.user = req.user.id;

    // Ensure vehicleNumber is set
    if (!req.body.vehicleNumber) {
      return res.status(400).json({
        success: false,
        message: 'Vehicle number is required',
      });
    }

    // Check if vehicle number already exists (check both fields for compatibility)
    const existingVehicle = await Vehicle.findOne({
      $or: [
        { vehicleNumber: req.body.vehicleNumber },
        { licensePlate: req.body.vehicleNumber }
      ]
    });

    if (existingVehicle) {
      return res.status(400).json({
        success: false,
        message: 'Vehicle with this number already exists',
      });
    }

    // Set both fields for compatibility
    req.body.licensePlate = req.body.vehicleNumber;

    const vehicle = await Vehicle.create(req.body);

    res.status(201).json({
      success: true,
      data: vehicle,
    });
  } catch (error) {
    console.error('Error creating vehicle:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Update vehicle
// @route   PUT /api/vehicles/:id
// @access  Private
exports.updateVehicle = async (req, res) => {
  try {
    let vehicle = await Vehicle.findById(req.params.id);

    if (!vehicle) {
      return res.status(404).json({
        success: false,
        message: `Vehicle not found with id of ${req.params.id}`,
      });
    }

    // Make sure user owns vehicle
    if (vehicle.user.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: `User ${req.user.id} is not authorized to update this vehicle`,
      });
    }

    vehicle = await Vehicle.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true,
    });

    res.status(200).json({
      success: true,
      data: vehicle,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Delete vehicle
// @route   DELETE /api/vehicles/:id
// @access  Private
exports.deleteVehicle = async (req, res) => {
  try {
    const vehicle = await Vehicle.findById(req.params.id);

    if (!vehicle) {
      return res.status(404).json({
        success: false,
        message: `Vehicle not found with id of ${req.params.id}`,
      });
    }

    // Make sure user owns vehicle
    if (vehicle.user.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: `User ${req.user.id} is not authorized to delete this vehicle`,
      });
    }

    await vehicle.deleteOne();

    res.status(200).json({
      success: true,
      data: {},
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get vehicle by number
// @route   GET /api/vehicles/number/:vehicleNumber
// @access  Private/Operator
exports.getVehicleByNumber = async (req, res) => {
  try {
    // Check both fields for compatibility
    const vehicle = await Vehicle.findOne({
      $or: [
        { vehicleNumber: req.params.vehicleNumber },
        { licensePlate: req.params.vehicleNumber }
      ]
    }).populate('user', 'name email phone');

    if (!vehicle) {
      return res.status(404).json({
        success: false,
        message: `Vehicle not found with number ${req.params.vehicleNumber}`,
      });
    }

    res.status(200).json({
      success: true,
      data: vehicle,
    });
  } catch (error) {
    console.error('Error finding vehicle by number:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};
