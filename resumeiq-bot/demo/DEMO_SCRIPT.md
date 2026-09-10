# ResumeIQ Bot — 2-Minute Live Demo Script

## Setup
1. Run `npm start`.
2. Run `ngrok http 3000`.
3. Configure Meta WhatsApp webhook URL `/webhook/whatsapp` and matching verify token.

## Minute 1 — Single Resume Analysis
Send `Hi`, paste `demo/sample-jd.txt`, then upload a PDF/DOCX resume. Show the score, six dimension breakdown, missing skills, recommendations, and course links. Point out that WhatsApp output is split below 1,500 characters.

## Minute 2 — Differentiators
Explain deterministic, transparent scoring; JD-specific course links; MongoDB audit/session storage; optional Slack and Discord loaders. If the live connection fails, read `RECORDED_DEMO.txt`.
