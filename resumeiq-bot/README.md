# ResumeIQ Discord Bot

ResumeIQ is a Node.js ATS resume analyzer that runs through Discord slash commands. WhatsApp has been removed from the active application. The bot parses PDF, DOCX, and TXT resumes, scores them against a job description, identifies missing skills, and returns an ATS report in a Discord embed.

## Quick start

```bash
cd resumeiq-bot
npm install
cp .env.example .env
# edit .env with Discord values
npm test
npm run register:discord
npm start
```

## Discord commands

1. `/setjd description:<paste the full job description>`
2. `/analyze resume:<attach a PDF, DOCX, or TXT file>`
3. `/compare` reports that the individual Discord analysis flow is active.

## Create the Discord application

1. Open the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application**, name it `ResumeIQ`, and create it.
3. Open **Bot** in the left menu and click **Add Bot**.
4. Under the Bot page, click **Reset Token** or **Copy Token**. This is `DISCORD_TOKEN`. Treat it like a password and never commit it.
5. Open **OAuth2 → General** and copy **Application ID**. This is `DISCORD_CLIENT_ID`.
6. Copy your Discord server ID for `DISCORD_GUILD_ID`: enable **User Settings → Advanced → Developer Mode**, right-click your server, and choose **Copy Server ID**.
7. Invite the bot through **OAuth2 → URL Generator**. Select the `bot` and `applications.commands` scopes and grant `Send Messages`, `Embed Links`, and `Attach Files`. Open the generated URL and select your server.

## Environment

```env
PORT=3000
NODE_ENV=development
MONGODB_URI=mongodb://localhost:27017/resumeiq
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
ENABLE_DISCORD=true
DISCORD_TOKEN=the_token_copied_from_the_Bot_page
DISCORD_CLIENT_ID=the_Application_ID
DISCORD_GUILD_ID=the_server_ID
ENABLE_SLACK=false
```

`DISCORD_TOKEN` is issued on the Bot page. `DISCORD_CLIENT_ID` is the Application ID, not the bot token. `DISCORD_GUILD_ID` is the ID of the server where you want the commands registered.

## Register commands and run

```bash
npm run register:discord
npm start
```

Guild commands usually appear quickly. Global commands can take longer to propagate if `DISCORD_GUILD_ID` is omitted. The local health endpoint is available at `http://localhost:3000/health`.

MongoDB and OpenAI are optional for local testing. Without MongoDB, sessions use an in-memory fallback. Without OpenAI, the deterministic ATS engine still produces a complete report.

## Security

Never paste your bot token into chat or GitHub. If exposed, return to **Developer Portal → Bot** and reset it immediately. Keep `.env` local; only commit `.env.example`.
