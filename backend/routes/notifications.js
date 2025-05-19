const express = require('express');
const {
  getUserNotifications,
  getNotification,
  createNotification,
  markAsRead,
  markAllAsRead,
  deleteNotification,
} = require('../controllers/notificationController');
const { protect, authorize } = require('../middleware/auth');

const router = express.Router();

router.use(protect);

// User routes
router.route('/').get(getUserNotifications);
router.route('/:id').get(getNotification).delete(deleteNotification);
router.route('/:id/read').put(markAsRead);
router.route('/read-all').put(markAllAsRead);

// Admin routes
router.route('/').post(authorize('admin'), createNotification);

module.exports = router;
