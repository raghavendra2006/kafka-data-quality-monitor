# ResumeIQ Discord Bot — 2-Minute Demo

## Setup

1. Copy `.env.example` to `.env` and add the Discord bot token, application ID, and server ID.
2. Run `npm install`, `npm run register:discord`, and `npm start`.
3. Confirm the bot is online in the Discord server.

## Demo flow

1. Run `/setjd` and paste `demo/sample-jd.txt` into the description option.
2. Run `/analyze` and attach a PDF, DOCX, or TXT resume.
3. Show the ATS score, score breakdown, matching strengths, missing skills, improvement tips, course links, and verdict in the Discord embed.
4. Explain that MongoDB and OpenAI are optional; the deterministic scoring engine works without them.
5. If the live bot is unavailable, run `npm run demo` and use `demo/RECORDED_DEMO.txt`.
