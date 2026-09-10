const {env}=require('../config/env');
const {withRetry}=require('./retryHandler');
async function enhance(resume,jd,preliminary){
 const fallback={improvementTips:defaultTips(preliminary),implicitMatches:[],verdict:preliminary.score>=75?'Strong Match — apply with confidence.':preliminary.score>=50?'Moderate Match — address critical gaps first.':'Weak Match — significant rework needed.',adjustedScore:preliminary.score};
 if(!env.openaiKey||env.openaiKey.includes('your_'))return fallback;
 try{const OpenAI=require('openai');const client=new OpenAI({apiKey:env.openaiKey});const out=await withRetry(()=>client.chat.completions.create({model:env.openaiModel,response_format:{type:'json_object'},messages:[{role:'system',content:'You are an expert ATS evaluation system. Return JSON with improvementTips string[], implicitMatches string[], verdict string, adjustedScore number within ±5.'},{role:'user',content:JSON.stringify({resume:resume.text,jd:jd.text,preliminary})}]}),{maxRetries:2,baseDelay:250});const content=out?.choices?.[0]?.message?.content;if(!content)return fallback;const parsed=JSON.parse(content);return {...fallback,...parsed,adjustedScore:Math.max(preliminary.score-5,Math.min(preliminary.score+5,Number(parsed.adjustedScore??preliminary.score)))};}catch(error){return {...fallback,providerFallback:true};}
}
function defaultTips(a){const t=[];if(a.missingCritical.length)t.push(`Add evidence for required skills: ${a.missingCritical.join(', ')}.`);if(a.missingImportant.length)t.push(`Consider adding preferred skills: ${a.missingImportant.join(', ')}.`);t.push('Add quantified achievements with measurable outcomes.','Tailor the summary and job title to the target role.','Use standard ATS-readable section headings.');return t.slice(0,7)}
module.exports={enhance};
