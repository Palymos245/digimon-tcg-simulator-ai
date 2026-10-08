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


## Local test setup

1. Start Project Drasil locally from the repository root with Docker Desktop:
   \`docker compose up -d\`

2. Confirm the simulator is reachable at:
   \`http://localhost:5173\`

3. In the \`ai\` directory, copy the supplied environment template to \`.env\` and set:
   - a unique \`BOT_USERNAME\`
   - any bot password/recovery question values
   - \`DECK_PATH=./data/beelzex_deck.json\`
   - \`OPENAI_API_KEY\`
   - \`OPENAI_MODEL\`

4. From the \`ai\` directory, install the existing bot requirements:
   \`python -m pip install -r requirements.txt\`

5. Start the LLM bot:
   \`python start_llm_bot.py\`

6. Open the simulator in the browser and invite the bot account. The bot uses the existing Beelzemon X Antibody deck from \`data/beelzex_deck.json\`.

The bot is intentionally still on the \`llm-agent-v1\` branch. Do not merge it into \`main\` until the first live match is successful.
