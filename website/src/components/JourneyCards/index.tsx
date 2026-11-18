import React from 'react';
import Link from '@docusaurus/Link';
import styles from './styles.module.css';

interface BentoItem {
  title: string;
  category: string;
  description: string;
  icon: string;
  link: string;
  featured?: boolean;
  tag?: string;
}

const CARDS: BentoItem[] = [
  {
    title: 'Closed Learning Loop',
    category: 'Memory & Intelligence',
    description: 'Creates skills from experience, refines them through usage nudges, and maintains persistent cross-session memory with Honcho dialectic modeling.',
    icon: '🧠',
    link: '/user-guide/features/memory',
    featured: true,
    tag: 'Core Innovation',
  },
  {
    title: 'Interactive TUI & Desktop',
    category: 'User Interface',
    description: 'Drive Hermes through a terminal UI with React/Ink session orchestration or the Electron Desktop multi-connection workspace.',
    icon: '🖥️',
    link: '/user-guide/desktop',
    tag: 'Desktop & TUI',
  },
  {
    title: '20+ Messaging Platforms',
    category: 'Universal Gateway',
    description: 'One gateway connects your agent to Telegram, Discord, Slack, WhatsApp, Teams, Google Chat, Matrix, and SMS simultaneously.',
    icon: '💬',
    link: '/user-guide/messaging/index',
    tag: 'Omnichannel',
  },
  {
    title: 'Bot Mode Teams',
    category: 'Multi-Agent',
    description: 'Assemble durable teams of specialized bots with distinct models, memories, and schedules collaborating in group chats via @mentions.',
    icon: '🤖',
    link: '/user-guide/bot-mode',
  },
  {
    title: 'Automated Cron & Kanban',
    category: 'Automation',
    description: 'Built-in cron scheduling delivering reports anywhere, paired with Kanban worker lanes and subagent delegation pipelines.',
    icon: '⚡',
    link: '/user-guide/features/cron',
  },
  {
    title: 'Extensible Skills & MCP',
    category: 'Ecosystem',
    description: 'Connect to any Model Context Protocol (MCP) server or install portable skills from the open community Skills Hub.',
    icon: '🔌',
    link: '/skills',
  },
];

export default function JourneyCards(): React.JSX.Element {
  return (
    <div className={styles.bentoGrid}>
      {CARDS.map((card, idx) => (
        <Link
          key={idx}
          to={card.link}
          className={`${styles.card} ${card.featured ? styles.featuredCard : ''}`}
        >
          <div className={styles.cardHeader}>
            <span className={styles.icon}>{card.icon}</span>
            {card.tag && <span className={styles.tag}>{card.tag}</span>}
          </div>
          <div className={styles.category}>{card.category}</div>
          <h3 className={styles.title}>{card.title}</h3>
          <p className={styles.description}>{card.description}</p>
          <div className={styles.cardFooter}>
            <span className={styles.arrowLink}>Learn more →</span>
          </div>
        </Link>
      ))}
    </div>
  );
}

