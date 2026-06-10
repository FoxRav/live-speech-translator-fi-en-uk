import { useEffect, useRef } from "react";
import type { TranslationEntry, UiSettings } from "./types";

const SCROLL_DURATION_MS = 1400;

function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2;
}

function smoothScrollToBottom(element: HTMLElement, durationMs: number): () => void {
  const startTime = performance.now();
  let rafId = 0;
  let cancelled = false;

  const step = (now: number) => {
    if (cancelled) {
      return;
    }

    const progress = Math.min((now - startTime) / durationMs, 1);
    const liveTarget = Math.max(0, element.scrollHeight - element.clientHeight);
    const followStrength = 0.06 + easeInOutCubic(progress) * 0.12;
    element.scrollTop += (liveTarget - element.scrollTop) * followStrength;

    if (progress < 1) {
      rafId = requestAnimationFrame(step);
      return;
    }

    element.scrollTop = liveTarget;
  };

  rafId = requestAnimationFrame(step);
  return () => {
    cancelled = true;
    cancelAnimationFrame(rafId);
  };
}

interface TranslationDisplayProps {
  entries: TranslationEntry[];
  settings: UiSettings;
  presentationMode?: boolean;
}

function LanguageRows({
  entry,
  settings,
}: {
  entry: TranslationEntry;
  settings: UiSettings;
}) {
  return (
    <>
      {settings.showUk && (
        <div className="language-row uk-row">
          <div className="language-text uk">{entry.uk}</div>
        </div>
      )}
      {settings.showEn && (
        <div className="language-row en-row">
          <div className="language-text en">{entry.en}</div>
        </div>
      )}
      {settings.showFi && (
        <div className="language-row fi-row">
          <div className="language-text fi">{entry.fi}</div>
        </div>
      )}
    </>
  );
}

export function TranslationDisplay({
  entries,
  settings,
  presentationMode = false,
}: TranslationDisplayProps) {
  const feedRef = useRef<HTMLDivElement>(null);
  const lastTimestampRef = useRef<string | null>(null);
  const cancelScrollRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    const feed = feedRef.current;
    if (!feed || entries.length === 0) {
      return;
    }

    const latest = entries[entries.length - 1];
    if (lastTimestampRef.current === latest.timestamp) {
      return;
    }
    lastTimestampRef.current = latest.timestamp;

    cancelScrollRef.current?.();
    cancelScrollRef.current = null;

    const scrollToLatest = () => {
      cancelScrollRef.current = smoothScrollToBottom(feed, SCROLL_DURATION_MS);
    };

    requestAnimationFrame(() => {
      requestAnimationFrame(scrollToLatest);
    });

    return () => {
      cancelScrollRef.current?.();
      cancelScrollRef.current = null;
    };
  }, [entries]);

  const placeholderSize = settings.showUk ? "uk" : settings.showEn ? "en" : "fi";

  return (
    <div
      className={`display-stage ${presentationMode ? "presentation" : ""}`}
      ref={feedRef}
    >
      <div className="translation-feed">
        {entries.length === 0 ? (
          <div className="feed-item feed-placeholder">
            <div className={`language-text placeholder ${placeholderSize}`}>
              Odottaa puhetta...
            </div>
          </div>
        ) : (
          entries.map((entry) => (
              <article key={entry.timestamp} className="feed-item">
                <LanguageRows entry={entry} settings={settings} />
              </article>
            ))
        )}
      </div>
    </div>
  );
}
