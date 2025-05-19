const mongoose = require('mongoose');

const NotificationSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    title: {
      type: String,
      required: [true, 'Please add a title'],
    },
    message: {
      type: String,
      required: [true, 'Please add a message'],
    },
    type: {
      type: String,
      enum: ['ticket', 'reservation', 'payment', 'system', 'other'],
      default: 'system',
    },
    relatedTo: {
      type: mongoose.Schema.Types.ObjectId,
      refPath: 'onModel',
    },
    onModel: {
      type: String,
      enum: ['Ticket', 'Vehicle', 'Zone'],
    },
    isRead: {
      type: Boolean,
      default: false,
    },
  },
  {
    timestamps: true,
  }
);

module.exports = mongoose.model('Notification', NotificationSchema);
