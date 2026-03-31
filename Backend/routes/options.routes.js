const router = require("express").Router();
const { getOptions } = require("../controllers/options.controller");

router.get("/", getOptions);

module.exports = router;