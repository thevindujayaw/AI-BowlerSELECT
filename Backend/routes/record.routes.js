const express = require("express");
const router = express.Router();

const controller = require("../controllers/record.controller");
const middleware = require("../middleware/auth.middleware");



const protect = middleware.protect;

router.post("/", protect, controller.createRecord);
router.get("/", protect, controller.getAllRecords);
router.get("/:id", protect, controller.getRecordById);
router.put("/:id", protect, controller.updateRecord);
router.delete("/:id", protect, controller.deleteRecord);

module.exports = router;
