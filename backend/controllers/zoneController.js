const Zone = require('../models/Zone');

// @desc    Get all zones
// @route   GET /api/zones
// @access  Public
exports.getZones = async (req, res) => {
  try {
    // Only return approved zones for regular users
    let query = {};
    if (req.user && req.user.role === 'user') {
      query.status = 'approved';
    }

    const zones = await Zone.find(query).populate('operator', 'name email phone');

    res.status(200).json({
      success: true,
      count: zones.length,
      data: zones,
    });
  } catch (error) {
    console.error('Error in getZones:', error.message);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get operator zones
// @route   GET /api/zones/operator
// @access  Private/Operator
exports.getOperatorZones = async (req, res) => {
  try {
    const zones = await Zone.find({ operator: req.user.id });

    res.status(200).json({
      success: true,
      count: zones.length,
      data: zones,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get single zone
// @route   GET /api/zones/:id
// @access  Public
exports.getZone = async (req, res) => {
  try {
    // Check if we have mock data (database connection failed)
    if (req.mockZones) {
      console.log('Using mock data for single zone');

      // Find the zone in mock data
      const zone = req.mockZones.find(z => z._id === req.params.id);

      if (!zone) {
        return res.status(404).json({
          success: false,
          message: `Zone not found with id of ${req.params.id}`,
        });
      }

      // Check if zone is approved or user is admin/operator
      if (
        zone.status !== 'approved' &&
        (!req.user || (req.user.role !== 'admin' && req.user.id !== zone.operator._id))
      ) {
        return res.status(403).json({
          success: false,
          message: 'Not authorized to access this zone',
        });
      }

      return res.status(200).json({
        success: true,
        data: zone,
      });
    }

    const zone = await Zone.findById(req.params.id).populate(
      'operator',
      'name email phone'
    );

    if (!zone) {
      return res.status(404).json({
        success: false,
        message: `Zone not found with id of ${req.params.id}`,
      });
    }

    // Check if zone is approved or user is admin/operator
    if (
      zone.status !== 'approved' &&
      (!req.user || (req.user.role !== 'admin' && req.user.id !== zone.operator.toString()))
    ) {
      return res.status(403).json({
        success: false,
        message: 'Not authorized to access this zone',
      });
    }

    res.status(200).json({
      success: true,
      data: zone,
    });
  } catch (error) {
    console.error('Error in getZone:', error.message);

    // Use mock data as fallback
    if (req.mockZones) {
      console.log('Using mock data as fallback after error');

      // Find the zone in mock data
      const zone = req.mockZones.find(z => z._id === req.params.id);

      if (!zone) {
        return res.status(404).json({
          success: false,
          message: `Zone not found with id of ${req.params.id}`,
        });
      }

      return res.status(200).json({
        success: true,
        data: zone,
      });
    }

    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Create zone
// @route   POST /api/zones
// @access  Private/Operator
exports.createZone = async (req, res) => {
  try {
    // Add operator to req.body
    req.body.operator = req.user.id;

    const zone = await Zone.create(req.body);

    res.status(201).json({
      success: true,
      data: zone,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Update zone
// @route   PUT /api/zones/:id
// @access  Private/Operator or Admin
exports.updateZone = async (req, res) => {
  try {
    let zone = await Zone.findById(req.params.id);

    if (!zone) {
      return res.status(404).json({
        success: false,
        message: `Zone not found with id of ${req.params.id}`,
      });
    }

    // Make sure user is zone operator or admin
    if (zone.operator.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: `User ${req.user.id} is not authorized to update this zone`,
      });
    }

    // If user is operator, they cannot update status
    if (req.user.role === 'operator' && req.body.status) {
      delete req.body.status;
    }

    zone = await Zone.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true,
    });

    res.status(200).json({
      success: true,
      data: zone,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Delete zone
// @route   DELETE /api/zones/:id
// @access  Private/Admin
exports.deleteZone = async (req, res) => {
  try {
    const zone = await Zone.findById(req.params.id);

    if (!zone) {
      return res.status(404).json({
        success: false,
        message: `Zone not found with id of ${req.params.id}`,
      });
    }

    // Only admin can delete zones
    if (req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: 'Not authorized to delete zones',
      });
    }

    await zone.deleteOne();

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

// @desc    Update zone status
// @route   PUT /api/zones/:id/status
// @access  Private/Admin
exports.updateZoneStatus = async (req, res) => {
  try {
    const { status } = req.body;

    if (!status || !['pending', 'approved', 'rejected'].includes(status)) {
      return res.status(400).json({
        success: false,
        message: 'Please provide a valid status',
      });
    }

    const zone = await Zone.findByIdAndUpdate(
      req.params.id,
      { status },
      {
        new: true,
        runValidators: true,
      }
    );

    if (!zone) {
      return res.status(404).json({
        success: false,
        message: `Zone not found with id of ${req.params.id}`,
      });
    }

    res.status(200).json({
      success: true,
      data: zone,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};
