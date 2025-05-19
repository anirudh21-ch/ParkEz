const express = require('express');
const {
  getZones,
  getOperatorZones,
  getZone,
  createZone,
  updateZone,
  deleteZone,
  updateZoneStatus,
} = require('../controllers/zoneController');
const { protect, authorize } = require('../middleware/auth');

const router = express.Router();

// Public routes
router.route('/').get(getZones);
router.route('/:id').get(getZone);

// Protected routes
router.use(protect);

// Operator routes
router.route('/operator').get(authorize('operator'), getOperatorZones);
router.route('/').post(authorize('operator'), createZone);
router.route('/:id').put(authorize('operator', 'admin'), updateZone);

// Admin routes
router.route('/:id').delete(authorize('admin'), deleteZone);
router.route('/:id/status').put(authorize('admin'), updateZoneStatus);

module.exports = router;
