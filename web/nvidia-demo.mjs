import fs from 'node:fs';
import path from 'node:path';

// Read NVIDIA_API_KEY from .env if not in process.env
let apiKey = process.env.NVIDIA_API_KEY;
if (!apiKey && fs.existsSync('.env')) {
  const envContent = fs.readFileSync('.env', 'utf8');
  const match = envContent.match(/NVIDIA_API_KEY=(.+)/);
  if (match) apiKey = match[1].trim();
}

if (!apiKey) {
  console.error('Error: NVIDIA_API_KEY is not set in environment or .env');
  process.exit(1);
}

const payload = {
  model: 'meta/llama-3.2-11b-vision-instruct',
  messages: [
    { role: 'system', content: 'You are a helpful coding assistant.' },
    { role: 'user', content: 'Write a quicksort function in TypeScript with a brief explanation.' }
  ],
  temperature: 0.2,
  top_p: 0.7,
  max_tokens: 512
};

console.log('Sending request to NVIDIA NIM (meta/llama-3.2-11b-vision-instruct)...');

try {
  const response = await fetch('https://integrate.api.nvidia.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status} ${response.statusText}: ${errorText}`);
  }

  const data = await response.json();
  console.log('\n--- Response from NVIDIA NIM ---');
  console.log(data.choices[0]?.message?.content);
  console.log('\n--- Usage ---');
  console.log(data.usage);
} catch (err) {
  console.error('NVIDIA AI Request failed:', err);
}
