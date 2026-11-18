import React, { useState } from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import styles from './styles.module.css';

export default function HeroBanner(): React.JSX.Element {
  const [isPlaying, setIsPlaying] = useState(false);
  const posterUrl = useBaseUrl('/img/docs/tui-session-orchestrator/session-orchestrator.png');
  const videoUrl = useBaseUrl('/img/docs/tui-session-orchestrator/session-orchestrator-demo.mp4');

  return (
    <section className={styles.heroWrapper}>
      <div className={styles.badge}>
        <span className={styles.badgePulse}></span>
        Autonomous • Self-Improving • 20+ Platforms
      </div>

      <h1 className={styles.heroTitle}>
        The Self-Improving <span className={styles.highlight}>AI Agent</span>
      </h1>

      <p className={styles.heroSubtitle}>
        Hermes creates skills from experience, improves them during use, and remembers across sessions.
        Run the exact same agent core across your terminal, desktop app, and 20+ messaging platforms.
      </p>

      <div className={styles.ctaGroup}>
        <Link to="/getting-started/installation" className={styles.primaryButton}>
          Get Started in 60s →
        </Link>
        <Link to="/user-guide/desktop" className={styles.secondaryButton}>
          Hermes Desktop
        </Link>
        <a
          href="https://github.com/NousResearch/hermes-agent"
          target="_blank"
          rel="noopener noreferrer"
          className={styles.ghostButton}
        >
          ⭐ GitHub
        </a>
      </div>

      <div className={styles.mediaContainer}>
        <div className={styles.mediaHeader}>
          <div className={styles.windowDots}>
            <span className={`${styles.dot} ${styles.dotRed}`}></span>
            <span className={`${styles.dot} ${styles.dotYellow}`}></span>
            <span className={`${styles.dot} ${styles.dotGreen}`}></span>
          </div>
          <div className={styles.mediaTitle}>hermes --tui • Session Orchestrator</div>
        </div>

        <div className={styles.mediaBody} onClick={() => !isPlaying && setIsPlaying(true)}>
          {!isPlaying ? (
            <div className={styles.posterOverlay}>
              <img
                src={posterUrl}
                alt="Hermes TUI Session Orchestrator"
                className={styles.posterImage}
              />
              <button
                type="button"
                className={styles.playButton}
                aria-label="Play Hermes 30s demonstration video"
              >
                <span className={styles.playIcon}>▶</span>
                <span>Watch 30s Demo</span>
              </button>
            </div>
          ) : (
            <video
              src={videoUrl}
              controls
              autoPlay
              className={styles.videoPlayer}
            >
              Your browser does not support the video tag.
            </video>
          )}
        </div>
      </div>
    </section>
  );
}

