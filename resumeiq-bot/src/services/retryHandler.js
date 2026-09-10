const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function withRetry(fn,{maxRetries=3,baseDelay=1000,onFailure,shouldRetry=()=>true}={}){let attempt=0;while(true){try{return await fn(attempt)}catch(err){if(!shouldRetry(err)||attempt>=maxRetries){if(onFailure)await onFailure(err);throw err}const h=err.headers||{};const ra=h['retry-after']||h['Retry-After'];const delay=ra?(Number(ra)*1000):baseDelay*Math.pow(2,attempt);attempt++;await sleep(delay)}}}
module.exports={withRetry,sleep};
