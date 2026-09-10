require('dotenv').config();
const bool=v=>String(v||'false').toLowerCase()==='true';
const env={port:Number(process.env.PORT||3000),nodeEnv:process.env.NODE_ENV||'development',mongoUri:process.env.MONGODB_URI||'',openaiKey:process.env.OPENAI_API_KEY||'',openaiModel:process.env.OPENAI_MODEL||'gpt-4o-mini',enableSlack:bool(process.env.ENABLE_SLACK),enableDiscord:bool(process.env.ENABLE_DISCORD),slack:{botToken:process.env.SLACK_BOT_TOKEN||'',signingSecret:process.env.SLACK_SIGNING_SECRET||'',appToken:process.env.SLACK_APP_TOKEN||''},discord:{token:process.env.DISCORD_TOKEN||'',clientId:process.env.DISCORD_CLIENT_ID||'',guildId:process.env.DISCORD_GUILD_ID||''}};
function validateEnv(){const missing=[];if(env.enableDiscord&&!env.discord.token)missing.push('DISCORD_TOKEN');if(env.enableSlack&&!env.slack.botToken)missing.push('SLACK_BOT_TOKEN');if(missing.length)throw new Error(`Missing environment variables: ${missing.join(', ')}`);return env}
module.exports={env,validateEnv};
