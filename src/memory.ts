import "dotenv/config";
import Supermemory from "supermemory";

if (!process.env.SUPERMEMORY_API_KEY) {
  throw new Error(
    "SUPERMEMORY_API_KEY is not set. Copy .env.example to .env and add your key.",
  );
}

// Reads SUPERMEMORY_API_KEY from the environment automatically.
export const client = new Supermemory();

/** Persist a piece of content to long-term memory, scoped to a container (user/project). */
export async function remember(content: string, containerTag: string) {
  return client.documents.add({ content, containerTag });
}

/** Recall memories relevant to a query, scoped to the same container. */
export async function recall(query: string, containerTag: string) {
  const { results } = await client.search.execute({ q: query, containerTag });
  return results;
}
