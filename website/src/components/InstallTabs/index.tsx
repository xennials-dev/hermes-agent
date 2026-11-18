import React, { useState } from 'react';
import Link from '@docusaurus/Link';
import styles from './styles.module.css';

interface InstallOption {
  id: string;
  label: string;
  badge?: string;
  command?: string;
  link?: string;
  linkText?: string;
  description: string;
}

const INSTALL_OPTIONS: InstallOption[] = [
  {
    id: 'unix',
    label: 'Linux / macOS / WSL2',
    badge: 'Fastest',
    command: 'curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash',
    description: 'Installs dependencies, provisions CLI, and links the hermes binary into your PATH.',
  },
  {
    id: 'windows',
    label: 'Windows (PowerShell)',
    command: 'iex (irm https://hermes-agent.nousresearch.com/install.ps1)',
    description: 'Native Windows installer via PowerShell with automatic environment setup.',
  },
  {
    id: 'desktop',
    label: 'Hermes Desktop',
    badge: 'GUI + CLI',
    link: 'https://hermes-agent.nousresearch.com/',
    linkText: 'Download Hermes Desktop (.exe / .dmg)',
    description: 'Bundles the full Electron interface, multi-agent workspace, and background gateway engine.',
  },
  {
    id: 'docker',
    label: 'Docker',
    command: 'docker run -it --rm -v ~/.hermes:/root/.hermes ghcr.io/nousresearch/hermes-agent:latest',
    description: 'Isolated container runtime with persistent host configuration mount.',
  },
  {
    id: 'nix',
    label: 'Nix & NixOS',
    command: 'nix run github:NousResearch/hermes-agent',
    description: 'Reproducible declarative setup for NixOS flakes and Darwin environments.',
  },
];

export default function InstallTabs(): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('unix');
  const [copied, setCopied] = useState<boolean>(false);

  const currentOption = INSTALL_OPTIONS.find((opt) => opt.id === activeTab) || INSTALL_OPTIONS[0];

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className={styles.installContainer}>
      <div className={styles.tabBar} role="tablist">
        {INSTALL_OPTIONS.map((opt) => (
          <button
            key={opt.id}
            role="tab"
            aria-selected={activeTab === opt.id}
            className={`${styles.tabButton} ${activeTab === opt.id ? styles.tabActive : ''}`}
            onClick={() => {
              setActiveTab(opt.id);
              setCopied(false);
            }}
          >
            <span>{opt.label}</span>
            {opt.badge && <span className={styles.tabBadge}>{opt.badge}</span>}
          </button>
        ))}
      </div>

      <div className={styles.codePanel}>
        {currentOption.command ? (
          <div className={styles.commandRow}>
            <span className={styles.promptSign}>$</span>
            <code className={styles.commandText}>{currentOption.command}</code>
            <button
              type="button"
              className={styles.copyBtn}
              onClick={() => handleCopy(currentOption.command!)}
              aria-label="Copy installation command"
            >
              {copied ? '✓ Copied' : 'Copy'}
            </button>
          </div>
        ) : (
          <div className={styles.linkRow}>
            <a
              href={currentOption.link}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.downloadLink}
            >
              ⬇ {currentOption.linkText}
            </a>
          </div>
        )}

        <div className={styles.panelFooter}>
          <p className={styles.description}>{currentOption.description}</p>
          <div className={styles.hintWrapper}>
            <span className={styles.hintBadge}>Next Step</span>
            <span>
              Run <code>hermes setup --portal</code> to configure models & tools. See{' '}
              <Link to="/getting-started/installation">Installation Guide →</Link>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

