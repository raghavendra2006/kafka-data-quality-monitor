# ResumeIQ Bot — AI-Powered ATS Resume Analyzer

An Express/MongoDB backend that analyzes resumes through WhatsApp, with optional Slack and Discord adapters. The core scorer is deterministic and explainable; OpenAI adds JD-specific improvement tips when configured and falls back safely when it is not.

```text
WhatsApp / Slack / Discord -> Webhooks or Events -> Express -> Parsers + ATS Engine
                                                    |-> MongoDB sessions/audit
                                                    |-> OpenAI enhancement
                                                    -> Chunker / Platform response
```

## Quick start

```bash
cd resumeiq-bot
npm install
cp .env.example .env
npm test
npm start
```

Configure Meta WhatsApp Cloud API with `GET/POST /webhook/whatsapp`; for local testing run `ngrok http 3000` and use the HTTPS URL in Meta. The verify token must match `WHATSAPP_VERIFY_TOKEN`. Incoming flow: send `Hi`, send a JD as text, then upload a PDF/DOCX/TXT resume. Use `new` or `reset` to clear the session.

Set `ENABLE_SLACK=true` or `ENABLE_DISCORD=true` only after adding that platform's credentials. The app remains WhatsApp-ready when optional credentials are absent. Run `npm run demo` for a local deterministic demonstration. Deploy to Railway or another Node host by setting the environment variables and using `npm start`.

## Notes

The integration design follows Meta's documented webhook payloads and retry behavior, Slack Bolt event handling, and Discord interaction responses. In production, use HTTPS, secret management, request signature validation, structured logging, and a persistent MongoDB instance.
