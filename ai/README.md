# Digimon TCG AI

The original BeelzemonXBot is a deterministic strategy bot. The new LLMBeelzemonBot keeps the simulator and card/effect code in charge of state changes, while an LLM chooses among high-level strategy routines during the Main Phase.

## LLM architecture

- Simulator/bot code owns memory, zones, phases, suspension, attacks, evolution, security, and card effects.
- The LLM chooses only one of the exposed strategic routines.
- The state view gives the LLM the bot's private hand plus public opponent information. Opponent hand/deck contents are intentionally not exposed.
- If an LLM call fails or returns an invalid choice, the bot falls back to the existing deterministic strategy order.

This is deliberately a first Level-2 integration. It is not yet a fully granular legal-action generator; later iterations can expose individual legal choices instead of the current strategy routines.

## Running the LLM bot

Run start_llm_bot.py from the ai directory with the same Project Drasil environment variables used by the existing bot, plus:

- OPENAI_API_KEY
- OPENAI_MODEL
- optional OPENAI_BASE_URL (defaults to https://api.openai.com/v1)
- optional OPENAI_TIMEOUT (defaults to 30 seconds)
- optional OPENAI_MAX_OUTPUT_TOKENS (defaults to 200)

The LLM adapter uses the OpenAI Responses API over the repository's existing requests dependency, so no additional Python package is required.
