import React, { useRef, useState, useEffect, useCallback } from "react";
import { Play, Pause, Volume2, VolumeX, Maximize, Minimize, RotateCcw, Loader2 } from "lucide-react";

export interface DocsVideoProps {
  src: string;
  poster?: string;
  title: string;
  autoPlay?: boolean;
  loop?: boolean;
  portrait?: boolean;
  className?: string;
}

export const DocsVideo: React.FC<DocsVideoProps> = ({
  src,
  poster,
  title,
  autoPlay = false,
  loop = false,
  portrait = false,
  className = "",
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const playerRef = useRef<HTMLDivElement | null>(null);
  const hideTimerRef = useRef<number | null>(null);
  const progressFrameRef = useRef<number | null>(null);

  const [enhanced, setEnhanced] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const [muted, setMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [controlsVisible, setControlsVisible] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [fullscreenSupported, setFullscreenSupported] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [scrubbing, setScrubbing] = useState(false);
  const [previewTime, setPreviewTime] = useState(0);
  const [previewPosition, setPreviewPosition] = useState(0);

  const formatTime = (seconds: number) => {
    if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
    const minutes = Math.floor(seconds / 60);
    const remaining = Math.floor(seconds % 60);
    return `${minutes}:${String(remaining).padStart(2, "0")}`;
  };

  const clearHideTimer = useCallback(() => {
    if (hideTimerRef.current !== null) {
      window.clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }
  }, []);

  const revealControls = useCallback(() => {
    setControlsVisible(true);
    clearHideTimer();
    hideTimerRef.current = window.setTimeout(() => setControlsVisible(false), 2400);
  }, [clearHideTimer]);

  const togglePlayback = async () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused || video.ended) {
      if (video.ended) video.currentTime = 0;
      setWaiting(true);
      try {
        await video.play();
      } catch {
        setWaiting(false);
        setPlaying(false);
      }
    } else {
      video.pause();
      setControlsVisible(true);
    }
  };

  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.muted && video.volume === 0) video.volume = 0.8;
    video.muted = !video.muted;
    setMuted(video.muted);
  };

  const seek = (event: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current;
    if (!video) return;
    const nextTime = Number(event.target.value);
    video.currentTime = nextTime;
    setCurrentTime(nextTime);
  };

  const updateScrubPreview = (event: React.PointerEvent<HTMLInputElement>, seekMainVideo = false) => {
    if (!duration) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
    const nextTime = ratio * duration;
    setPreviewing(true);
    setPreviewTime(nextTime);
    setPreviewPosition(ratio * 100);
    if (seekMainVideo) {
      const video = videoRef.current;
      if (video) {
        video.currentTime = nextTime;
        setCurrentTime(nextTime);
      }
    }
  };

  const cyclePlaybackRate = () => {
    const video = videoRef.current;
    if (!video) return;
    const rates = [1, 1.25, 1.5, 2];
    const currentIndex = rates.indexOf(video.playbackRate);
    const nextRate = rates[(currentIndex + 1) % rates.length];
    video.playbackRate = nextRate;
    setPlaybackRate(nextRate);
  };

  const toggleFullscreen = async () => {
    const player = playerRef.current;
    const video = videoRef.current as (HTMLVideoElement & { webkitEnterFullscreen?: () => void }) | null;
    if (!player || typeof document === "undefined") return;
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else if (player.requestFullscreen) {
        await player.requestFullscreen();
      } else if (video?.webkitEnterFullscreen) {
        video.webkitEnterFullscreen();
      }
    } catch {
      // Ignored if fullscreen rejected
    }
  };

  const handleKeyboard = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.target !== event.currentTarget) return;
    const video = videoRef.current;
    if (!video) return;
    if (event.key === " " || event.key === "Enter") {
      event.preventDefault();
      togglePlayback();
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      video.currentTime = Math.max(0, video.currentTime - 5);
      revealControls();
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      video.currentTime = Math.min(duration || video.duration || 0, video.currentTime + 5);
      revealControls();
    } else if (event.key.toLowerCase() === "m") {
      event.preventDefault();
      toggleMute();
      revealControls();
    } else if (event.key.toLowerCase() === "f") {
      event.preventDefault();
      toggleFullscreen();
    }
  };

  useEffect(() => {
    setEnhanced(true);
    const video = videoRef.current as (HTMLVideoElement & { webkitEnterFullscreen?: () => void }) | null;
    setFullscreenSupported(Boolean(playerRef.current?.requestFullscreen || video?.webkitEnterFullscreen));
    return () => {
      clearHideTimer();
    };
  }, [clearHideTimer]);

  useEffect(() => {
    if (typeof document === "undefined") return undefined;
    const syncFullscreen = () => setFullscreen(document.fullscreenElement === playerRef.current);
    document.addEventListener("fullscreenchange", syncFullscreen);
    return () => document.removeEventListener("fullscreenchange", syncFullscreen);
  }, []);

  useEffect(() => {
    clearHideTimer();
    if (!playing) return undefined;
    hideTimerRef.current = window.setTimeout(() => setControlsVisible(false), 2400);
    return clearHideTimer;
  }, [playing, clearHideTimer]);

  useEffect(() => {
    if (!playing) return undefined;
    const updateProgress = () => {
      const video = videoRef.current;
      if (video && !video.paused) setCurrentTime(video.currentTime);
      progressFrameRef.current = window.requestAnimationFrame(updateProgress);
    };
    progressFrameRef.current = window.requestAnimationFrame(updateProgress);
    return () => {
      if (progressFrameRef.current !== null) window.cancelAnimationFrame(progressFrameRef.current);
      progressFrameRef.current = null;
    };
  }, [playing]);

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
  const replaying = duration > 0 && currentTime >= duration - 0.15;

  return (
    <div
      className={`relative w-full overflow-hidden rounded-xl bg-black/90 shadow-2xl border border-white/10 ${
        portrait ? "max-w-xs mx-auto aspect-[9/16]" : "aspect-video"
      } ${className}`}
    >
      <div
        ref={playerRef}
        className="group relative w-full h-full flex items-center justify-center outline-none select-none"
        role="region"
        aria-label={title}
        tabIndex={0}
        onKeyDown={handleKeyboard}
        onPointerMove={revealControls}
        onPointerLeave={() => setControlsVisible(false)}
        onFocus={revealControls}
        onBlur={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
            setControlsVisible(false);
          }
        }}
      >
        <video
          ref={videoRef}
          aria-label={title}
          src={src}
          poster={poster}
          autoPlay={autoPlay}
          loop={loop}
          playsInline
          preload="metadata"
          controls={!enhanced}
          className="w-full h-full object-contain cursor-pointer"
          onClick={togglePlayback}
          onDoubleClick={toggleFullscreen}
          onLoadedMetadata={(event) => {
            const nextDuration = event.currentTarget.duration || 0;
            setDuration(nextDuration);
            setMuted(event.currentTarget.muted);
          }}
          onDurationChange={(event) => setDuration(event.currentTarget.duration || 0)}
          onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          onPlaying={() => setWaiting(false)}
          onWaiting={() => setWaiting(true)}
          onCanPlay={() => setWaiting(false)}
          onEnded={() => {
            setPlaying(false);
            setControlsVisible(true);
          }}
          onVolumeChange={(event) => setMuted(event.currentTarget.muted)}
        />

        {enhanced && (
          <>
            {/* Hero Big Play / Replay Button */}
            {!playing && (currentTime <= 0.2 || replaying) && (
              <button
                type="button"
                className="absolute z-10 flex h-16 w-16 items-center justify-center rounded-full bg-black/60 text-white backdrop-blur-md transition-all duration-200 hover:scale-110 hover:bg-black/80 hover:text-teal-400 border border-white/20 shadow-lg cursor-pointer"
                onClick={togglePlayback}
                aria-label={replaying ? "Replay video" : "Play video"}
              >
                {replaying ? <RotateCcw className="h-7 w-7" /> : <Play className="h-7 w-7 fill-current translate-x-0.5" />}
              </button>
            )}

            {/* Spinner indicator */}
            {waiting && playing && (
              <div className="absolute z-10 flex items-center justify-center pointer-events-none">
                <Loader2 className="h-10 w-10 text-teal-400 animate-spin opacity-80" />
              </div>
            )}

            {/* Controls Bar Overlay */}
            <div
              className={`absolute inset-x-0 bottom-0 z-20 flex flex-col justify-end bg-gradient-to-t from-black/80 via-black/40 to-transparent p-3 sm:p-4 transition-opacity duration-300 ${
                controlsVisible || !playing ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
              }`}
            >
              {/* Floating Scrub Preview Time */}
              {previewing && (
                <div
                  className="pointer-events-none absolute -top-8 -translate-x-1/2 rounded bg-black/90 px-2 py-0.5 text-xs font-mono text-white/90 shadow border border-white/10"
                  style={{ left: `${previewPosition}%` }}
                >
                  {formatTime(previewTime)}
                </div>
              )}

              {/* Video Timeline / Progress Range Bar */}
              <div className="relative w-full flex items-center mb-2">
                <div className="absolute inset-x-0 h-1.5 rounded-full bg-white/20 overflow-hidden pointer-events-none">
                  <div
                    className="h-full bg-teal-400 transition-all duration-75"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <input
                  type="range"
                  min="0"
                  max={duration || 0}
                  step="0.01"
                  value={Math.min(currentTime, duration || 0)}
                  aria-label="Video progress"
                  aria-valuetext={`${formatTime(currentTime)} of ${formatTime(duration)}`}
                  onChange={seek}
                  onPointerEnter={(e) => updateScrubPreview(e)}
                  onPointerMove={(e) => updateScrubPreview(e, scrubbing || e.buttons === 1)}
                  onPointerDown={(e) => {
                    setScrubbing(true);
                    (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId);
                    updateScrubPreview(e, true);
                  }}
                  onPointerUp={(e) => {
                    setScrubbing(false);
                    if (e.pointerType !== "mouse") setPreviewing(false);
                  }}
                  onPointerCancel={() => {
                    setScrubbing(false);
                    setPreviewing(false);
                  }}
                  onPointerLeave={() => {
                    if (!scrubbing) setPreviewing(false);
                  }}
                  className="w-full h-3 opacity-0 cursor-pointer z-10"
                />
              </div>

              {/* Lower Controls Row */}
              <div className="flex items-center gap-3 text-white text-sm font-medium">
                {/* Play / Pause Toggle */}
                <button
                  type="button"
                  className="p-1.5 rounded-md hover:bg-white/15 text-white/90 hover:text-white transition-colors cursor-pointer"
                  onClick={togglePlayback}
                  aria-label={playing ? "Pause video" : "Play video"}
                >
                  {playing ? <Pause className="h-5 w-5 fill-current" /> : <Play className="h-5 w-5 fill-current" />}
                </button>

                {/* Mute Toggle */}
                <button
                  type="button"
                  className="p-1.5 rounded-md hover:bg-white/15 text-white/90 hover:text-white transition-colors cursor-pointer"
                  onClick={toggleMute}
                  aria-label={muted ? "Unmute video" : "Mute video"}
                >
                  {muted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                </button>

                {/* Timestamp */}
                <span className="text-xs font-mono text-white/80 tabular-nums select-none">
                  {formatTime(currentTime)} <span className="text-white/40">/</span> {formatTime(duration)}
                </span>

                <div className="flex-1" />

                {/* Rate Speed Toggle */}
                <button
                  type="button"
                  className="px-2 py-0.5 rounded text-xs font-mono font-semibold bg-white/10 hover:bg-white/20 text-white/90 hover:text-white transition-colors cursor-pointer border border-white/10"
                  onClick={cyclePlaybackRate}
                  aria-label={`Playback speed ${playbackRate} times`}
                >
                  {playbackRate}×
                </button>

                {/* Fullscreen Toggle */}
                {fullscreenSupported && (
                  <button
                    type="button"
                    className="p-1.5 rounded-md hover:bg-white/15 text-white/90 hover:text-white transition-colors cursor-pointer"
                    onClick={toggleFullscreen}
                    aria-label={fullscreen ? "Exit fullscreen" : "Enter fullscreen"}
                  >
                    {fullscreen ? <Minimize className="h-5 w-5" /> : <Maximize className="h-5 w-5" />}
                  </button>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
