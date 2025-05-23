const express = require('express');
const {
  getZones,
  getOperatorZones,
  getZone,
  createZone,
  updateZone,
  deleteZone,
  updateZoneStatus,
  getPendingZones,
  getZoneStats,
  getZoneCount,
  getPendingZoneCount,
} = require('../controllers/zoneController');
const { protect, authorize } = require('../middleware/auth');

const router = express.Router();

// Protected routes
router.use(protect);

// Admin count routes - these need to be before the :id routes to avoid conflicts
router.get('/count', authorize('admin'), getZoneCount);
router.get('/pending', authorize('admin'), getPendingZones);
router.get('/pending/count', authorize('admin'), getPendingZoneCount);

// Operator routes
router.route('/operator').get(authorize('operator'), getOperatorZones);
router.route('/').get(getZones);
router.route('/').post(authorize('operator'), createZone);

// Routes with ID parameter
router.route('/:id').get(getZone);
router.route('/:id').put(authorize('operator', 'admin'), updateZone);
router.route('/:id').delete(authorize('admin'), deleteZone);
router.route('/:id/status').put(authorize('admin'), updateZoneStatus);
router.route('/:id/stats').get(authorize('admin', 'operator'), getZoneStats);
router.route('/:id/approve').put(authorize('admin'), (req, res) => {
  if (!req.body) {
    req.body = {};
  }
  req.body.status = 'approved';
  updateZoneStatus(req, res);
});
router.route('/:id/reject').put(authorize('admin'), (req, res) => {
  if (!req.body) {
    req.body = {};
  }
  req.body.status = 'rejected';
  updateZoneStatus(req, res);
});

module.exports = router;
