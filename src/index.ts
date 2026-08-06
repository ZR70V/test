import { remember, recall } from "./memory.js";

const CONTAINER_TAG = process.env.SUPERMEMORY_CONTAINER_TAG ?? "default-project";

/** Example: recall relevant memory for a message, then persist the message itself. */
async function handleMessage(userMessage: string) {
  const memories = await recall(userMessage, CONTAINER_TAG);
  console.log("Relevant memories:", memories);

  await remember(userMessage, CONTAINER_TAG);
  console.log("Stored message in memory.");
}

const message = process.argv.slice(2).join(" ") || "Hello, Supermemory!";
handleMessage(message).catch((err) => {
  console.error(err);
  process.exit(1);
});
