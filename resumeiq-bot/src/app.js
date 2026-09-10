const express=require('express');
const cors=require('cors');
const morgan=require('morgan');
const {env}=require('./config/env');
const {connectDatabase}=require('./config/database');
const {createDiscordClient}=require('./platforms/discord/discordHandler');
const app=express();
app.use(cors());
app.use(morgan('combined'));
app.use(express.json({limit:'2mb'}));
app.get('/health',(req,res)=>res.json({ok:true,service:'resumeiq-discord-bot',platform:'discord'}));
if(require.main===module){connectDatabase().catch(e=>console.error('MongoDB unavailable:',e.message));if(!env.enableDiscord)console.warn('ENABLE_DISCORD is false; set it to true to connect Discord.');else createDiscordClient();app.listen(env.port,()=>console.log(`ResumeIQ Discord bot health server listening on ${env.port}`))}
module.exports=app;
