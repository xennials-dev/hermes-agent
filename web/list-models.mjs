import fs from 'node:fs';

const env = fs.readFileSync('.env', 'utf8');
const key = env.match(/NVIDIA_API_KEY=(.+)/)[1].trim();

const res = await fetch('https://integrate.api.nvidia.com/v1/models', {
  headers: { Authorization: `Bearer ${key}` }
});
const data = await res.json();
const ids = data.data.map(m => m.id);
console.log('Total models:', ids.length);
console.log('\n--- Llama / Qwen / DeepSeek / Nemotron models ---');
ids.filter(id => id.includes('llama') || id.includes('deepseek') || id.includes('qwen') || id.includes('nemotron'))
   .forEach(id => console.log('-', id));
