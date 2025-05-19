const express = require('express');
const {
  getVehicles,
  getUserVehicles,
  getVehicle,
  createVehicle,
  updateVehicle,
  deleteVehicle,
  getVehicleByNumber,
} = require('../controllers/vehicleController');
const { protect, authorize } = require('../middleware/auth');

const router = express.Router();

router.use(protect);

// Admin routes
router.route('/').get(authorize('admin'), getVehicles);

// User routes
router.route('/user').get(getUserVehicles);
router.route('/').post(createVehicle);
router.route('/:id').get(getVehicle).put(updateVehicle).delete(deleteVehicle);

// Operator routes
router.route('/number/:vehicleNumber').get(authorize('operator', 'admin'), getVehicleByNumber);

module.exports = router;
