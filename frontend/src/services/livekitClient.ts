import { Room, RoomEvent } from "livekit-client";

const BACKEND_URL =
  import.meta.env.VITE_BACKEND_HTTP_URL || "http://localhost:5000";

export async function connectToLiveKit(
  roomName = "bhashaflow-main"
) {
  const response = await fetch(
    `${BACKEND_URL}/api/livekit/token?room=${encodeURIComponent(roomName)}`
  );

  if (!response.ok) {
    throw new Error("Failed to get LiveKit token");
  }

  const data = await response.json();

  const room = new Room();

  room.on(RoomEvent.Connected, () => {
    console.log("✅ Connected to LiveKit:", roomName);
  });

  room.on(RoomEvent.Disconnected, () => {
    console.log("❌ Disconnected from LiveKit");
  });

  await room.connect(data.url, data.token);

  return room;
}