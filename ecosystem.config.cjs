module.exports = {
  apps: [
    {
      name: 'hermes-agent',
      script: 'run_agent.py',
      interpreter: 'python3',
      cwd: '/opt/apps/hermes-agent',
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
        HERMES_PORT: '9118',
        HOST: '0.0.0.0'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: '/var/log/hermes-agent-error.log',
      out_file: '/var/log/hermes-agent-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};
