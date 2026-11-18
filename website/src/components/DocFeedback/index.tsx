import React, { useState } from 'react';
import styles from './styles.module.css';

interface DocFeedbackProps {
  pageTitle?: string;
}

export default function DocFeedback({ pageTitle }: DocFeedbackProps): React.JSX.Element {
  const [voted, setVoted] = useState<'yes' | 'no' | null>(null);

  return (
    <div className={styles.feedbackContainer}>
      <div className={styles.contentRow}>
        <span className={styles.question}>Was this documentation page helpful?</span>
        {!voted ? (
          <div className={styles.buttonGroup}>
            <button
              type="button"
              className={styles.voteBtn}
              onClick={() => setVoted('yes')}
              aria-label="Vote Yes, this page was helpful"
            >
              👍 Yes
            </button>
            <button
              type="button"
              className={styles.voteBtn}
              onClick={() => setVoted('no')}
              aria-label="Vote No, this page needs improvement"
            >
              👎 No
            </button>
          </div>
        ) : (
          <span className={styles.thankYou}>
            {voted === 'yes' ? '🎉 Thanks for your feedback!' : '🙏 Thanks! We will improve this.'}
          </span>
        )}
      </div>

      <div className={styles.subLinks}>
        <a
          href={`https://github.com/NousResearch/hermes-agent/issues/new?title=Docs%20feedback:%20${encodeURIComponent(
            pageTitle || 'General'
          )}`}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.githubLink}
        >
          Report an issue with this doc →
        </a>
      </div>
    </div>
  );
}

