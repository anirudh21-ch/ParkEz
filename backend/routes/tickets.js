const express = require('express');
const {
  getTickets,
  getUserTickets,
  getZoneTickets,
  getTicket,
  createTicket,
  checkoutTicket,
  getActiveTicketByVehicle,
} = require('../controllers/ticketController');
const { protect, authorize } = require('../middleware/auth');

const router = express.Router();

router.use(protect);

// Admin routes
router.route('/').get(authorize('admin'), getTickets);

// User routes
router.route('/user').get(getUserTickets);
router.route('/:id').get(getTicket);

// Operator routes
router.route('/zone/:zoneId').get(authorize('operator', 'admin'), getZoneTickets);
router.route('/vehicle/:vehicleNumber').get(authorize('operator', 'admin'), getActiveTicketByVehicle);
router.route('/').post(authorize('operator', 'admin'), createTicket);
router.route('/:id/checkout').put(authorize('operator', 'admin'), checkoutTicket);

module.exports = router;
