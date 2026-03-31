const express = require("express");
const router = express.Router();
const { protect } = require("../middleware/auth.middleware");
const { getAccountData, deletePrediction } = require("../controllers/account.controller");

router.get("/", protect, getAccountData);
router.delete("/predictions/:id", protect, deletePrediction);

module.exports = router;
