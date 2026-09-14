import { connectToLiveKit } from "./livekitClient";

connectToLiveKit()
  .then(() => {
    console.log("🎉 LiveKit connection test successful");
  })
  .catch((error) => {
    console.error("❌ LiveKit connection test failed:", error);
  });