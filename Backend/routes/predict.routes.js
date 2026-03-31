const express = require("express");
const router = express.Router();

const { protect } = require("../middleware/auth.middleware");
const { runPrediction, runPredictionPublic } = require("../controllers/predict.controller");

// POST /api/predict
router.post("/", protect, runPrediction);
router.post("/public", runPredictionPublic);

module.exports = router;
