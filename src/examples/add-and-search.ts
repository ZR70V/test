import { supermemory } from "../lib/supermemory.js";

// containerTag scopes memories to a single user so each user gets an
// isolated memory space. See https://supermemory.ai/docs/concepts/filtering
const containerTag = "user_demo";

async function main() {
  await supermemory.add({
    content: "The user prefers dark mode and TypeScript over JavaScript.",
    containerTag,
  });

  const response = await supermemory.search({
    q: "What does the user prefer?",
    containerTag,
  });

  console.log(response.results);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
