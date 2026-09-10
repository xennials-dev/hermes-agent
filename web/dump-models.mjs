import fs from 'node:fs';

const env = fs.readFileSync('.env', 'utf8');
const key = env.match(/NVIDIA_API_KEY=(.+)/)[1].trim();

const res = await fetch('https://integrate.api.nvidia.com/v1/models', {
  headers: { Authorization: `Bearer ${key}` }
});
const data = await res.json();
console.log('All models:');
data.data.forEach(m => console.log(m.id));
