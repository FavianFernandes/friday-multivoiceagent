require("dotenv").config();
const express = require("express");
const cors = require("cors");
const { AccessToken } = require("livekit-server-sdk");

const app = express();

app.use(cors());
app.use(express.json());

const PORT = 5000;

app.get("/", (req, res) => {
    res.send("Friday backend is running!");
});

// Generate a LiveKit access token for the frontend
app.get("/api/livekit/token", async (req, res) => {
    try {
        const roomName = req.query.room || "bhashaflow-main";
        const participantName =
            req.query.name || `user-${Date.now()}`;

        const apiKey = process.env.LIVEKIT_API_KEY;
        const apiSecret = process.env.LIVEKIT_API_SECRET;

        if (!apiKey || !apiSecret) {
            return res.status(500).json({
                error: "LiveKit credentials are not configured",
            });
        }

        const token = new AccessToken(apiKey, apiSecret, {
            identity: participantName,
            ttl: "1h",
        });

        token.addGrant({
            roomJoin: true,
            room: roomName,
            canPublish: true,
            canSubscribe: true,
        });

        const jwt = await token.toJwt();

        res.json({
            token: jwt,
            url: process.env.LIVEKIT_URL,
            room: roomName,
        });
    } catch (error) {
        console.error("Token generation error:", error);
        res.status(500).json({
            error: "Failed to generate LiveKit token",
        });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});