/* ==========================================================================
   WINNERTAINMENT.COM — App JavaScript
   Interactive Record Label Experience + Video Loop Autoplay Management
   Optimized for Maximum 60 FPS Performance, Zero Layout Thrashing
   ========================================================================== */

'use strict';

document.addEventListener('DOMContentLoaded', () => {

  // --- PRELOADER ---
  const preloader = document.getElementById('preloader');
  const hidePreloader = () => {
    if (preloader && !preloader.classList.contains('hidden')) {
      preloader.classList.add('hidden');
    }
  };

  if (document.readyState === 'complete') {
    hidePreloader();
  } else {
    window.addEventListener('load', () => setTimeout(hidePreloader, 300), { once: true });
    // Failsafe timeout
    setTimeout(hidePreloader, 1000);
  }

  // --- GPU-ACCELERATED CURSOR GLOW ---
  const cursorGlow = document.getElementById('cursorGlow');
  if (cursorGlow && window.matchMedia('(pointer: fine)').matches) {
    let mouseX = -500;
    let mouseY = -500;
    let glowTicking = false;

    window.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;

      if (!glowTicking) {
        glowTicking = true;
        requestAnimationFrame(() => {
          cursorGlow.style.transform = `translate3d(${mouseX}px, ${mouseY}px, 0) translate3d(-50%, -50%, 0)`;
          if (!cursorGlow.classList.contains('active')) {
            cursorGlow.classList.add('active');
          }
          glowTicking = false;
        });
      }
    }, { passive: true });

    document.addEventListener('mouseleave', () => {
      cursorGlow.classList.remove('active');
    });
  }

  // --- NAVBAR SCROLL & ACTIVE LINKS (THROTTLED WITH rAF) ---
  const navbar = document.getElementById('navbar');
  const scrollTop = document.getElementById('scrollTop');
  const navLinks = Array.from(document.querySelectorAll('.nav-link'));
  const sections = Array.from(document.querySelectorAll('section[id]'));

  let scrollTicking = false;

  function updateScrollState() {
    const scrollY = window.scrollY;

    if (navbar) {
      navbar.classList.toggle('scrolled', scrollY > 40);
    }
    if (scrollTop) {
      scrollTop.classList.toggle('visible', scrollY > 400);
    }

    // Active Section Detection
    let current = '';
    for (let i = 0; i < sections.length; i++) {
      const sec = sections[i];
      const sectionTop = sec.offsetTop - 140;
      const sectionHeight = sec.offsetHeight;
      if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
        current = sec.getAttribute('id');
        break;
      }
    }

    if (current) {
      navLinks.forEach((link) => {
        link.classList.toggle('active', link.getAttribute('href') === `#${current}`);
      });
    }

    scrollTicking = false;
  }

  window.addEventListener('scroll', () => {
    if (!scrollTicking) {
      scrollTicking = true;
      requestAnimationFrame(updateScrollState);
    }
  }, { passive: true });

  // Initial call
  updateScrollState();

  if (scrollTop) {
    scrollTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // --- MOBILE HAMBURGER MENU ---
  const hamburger = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobileMenu');
  const mobileLinks = document.querySelectorAll('.mobile-link');

  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      const isOpen = mobileMenu.classList.toggle('open');
      document.body.style.overflow = isOpen ? 'hidden' : '';
      if (hamburger.children.length >= 2) {
        hamburger.children[0].style.transform = isOpen ? 'rotate(45deg) translate(6px, 6px)' : '';
        hamburger.children[1].style.transform = isOpen ? 'rotate(-45deg) translate(6px, -6px)' : '';
      }
    });

    mobileLinks.forEach((link) => {
      link.addEventListener('click', () => {
        mobileMenu.classList.remove('open');
        document.body.style.overflow = '';
        if (hamburger.children.length >= 2) {
          hamburger.children[0].style.transform = '';
          hamburger.children[1].style.transform = '';
        }
      });
    });
  }

  // --- ANIMATED COUNTERS (TRIGGERED VIA INTERSECTION OBSERVER) ---
  const statsSection = document.querySelector('.hero-stats');
  const statNumbers = document.querySelectorAll('.hero-stat-num');
  let counted = false;

  function countUp() {
    if (counted) return;
    counted = true;

    statNumbers.forEach((stat) => {
      const target = parseInt(stat.getAttribute('data-count'), 10);
      if (isNaN(target)) return;
      const duration = 1800;
      const step = Math.max(1, Math.ceil(target / (duration / 25)));
      let current = 0;

      const timer = setInterval(() => {
        current += step;
        if (current >= target) {
          current = target;
          clearInterval(timer);
        }
        stat.textContent = current.toLocaleString();
      }, 25);
    });
  }

  if (statsSection && 'IntersectionObserver' in window) {
    const statsObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          countUp();
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.25 });
    statsObserver.observe(statsSection);
  } else {
    setTimeout(countUp, 400);
  }

  // --- MUSIC TRACK DATA & PLAYER BAR ---
  const tracks = [
    { id: 1, title: "Winner's Anthem", artist: "Da.Winner.Net Featured", duration: "3:45", color: "gradient-1" },
    { id: 2, title: "Only Winners Win", artist: "Winnertainment Records", duration: "4:12", color: "gradient-2" },
    { id: 3, title: "On Top", artist: "Da.Winner.Net Featured", duration: "3:28", color: "gradient-3" },
    { id: 4, title: "Grind Mode", artist: "Winnertainment Records", duration: "3:55", color: "gradient-4" },
    { id: 5, title: "Level Up", artist: "Da.Winner.Net Featured", duration: "4:01", color: "gradient-5" },
    { id: 6, title: "No Cap", artist: "Winnertainment Records", duration: "3:33", color: "gradient-6" }
  ];

  let currentTrackIndex = 0;
  let isPlaying = false;
  let progressInterval = null;
  let progressPercent = 0;

  const pTrack = document.getElementById('pTrack');
  const pArtist = document.getElementById('pArtist');
  const pbPlay = document.getElementById('pbPlay');
  const pbPlayIcon = document.getElementById('pbPlayIcon');
  const pbPrev = document.getElementById('pbPrev');
  const pbNext = document.getElementById('pbNext');
  const pbFill = document.getElementById('pbFill');
  const pbTime = document.getElementById('pbTime');
  const pbTotal = document.getElementById('pbTotal');
  const pbProgress = document.getElementById('pbProgress');
  const playerBarArt = document.querySelector('.player-bar-art');

  function loadTrack(index) {
    currentTrackIndex = index;
    const track = tracks[index];
    if (pTrack) pTrack.textContent = track.title;
    if (pArtist) pArtist.textContent = track.artist;
    if (pbTotal) pbTotal.textContent = track.duration;
    if (playerBarArt) {
      playerBarArt.className = `player-bar-art ${track.color}`;
    }
    progressPercent = 0;
    if (pbFill) pbFill.style.width = '0%';
    if (pbTime) pbTime.textContent = '0:00';
    if (pbProgress) pbProgress.setAttribute('aria-valuenow', '0');
  }

  function playTrack() {
    isPlaying = true;
    if (pbPlayIcon) {
      pbPlayIcon.className = 'fas fa-pause';
    }
    if (progressInterval) clearInterval(progressInterval);

    progressInterval = setInterval(() => {
      progressPercent += 0.5;
      if (progressPercent >= 100) {
        progressPercent = 0;
        nextTrack();
      }
      if (pbFill) pbFill.style.width = `${progressPercent}%`;
      if (pbProgress) pbProgress.setAttribute('aria-valuenow', Math.round(progressPercent).toString());

      // Update time string simulation
      const totalSec = 225;
      const curSec = Math.floor((progressPercent / 100) * totalSec);
      const mins = Math.floor(curSec / 60);
      const secs = curSec % 60;
      if (pbTime) pbTime.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }, 500);
  }

  function pauseTrack() {
    isPlaying = false;
    if (pbPlayIcon) {
      pbPlayIcon.className = 'fas fa-play';
    }
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
  }

  function togglePlay() {
    if (isPlaying) {
      pauseTrack();
    } else {
      playTrack();
    }
  }

  function prevTrack() {
    currentTrackIndex = (currentTrackIndex - 1 + tracks.length) % tracks.length;
    loadTrack(currentTrackIndex);
    playTrack();
  }

  function nextTrack() {
    currentTrackIndex = (currentTrackIndex + 1) % tracks.length;
    loadTrack(currentTrackIndex);
    playTrack();
  }

  if (pbPlay) pbPlay.addEventListener('click', togglePlay);
  if (pbPrev) pbPrev.addEventListener('click', prevTrack);
  if (pbNext) pbNext.addEventListener('click', nextTrack);

  // Click card play buttons
  const releaseCards = document.querySelectorAll('.release-card');
  releaseCards.forEach((card, idx) => {
    const playBtn = card.querySelector('.play-overlay');
    if (playBtn) {
      playBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        loadTrack(idx);
        playTrack();

        const vinyl = document.querySelector('.hero-vinyl');
        if (vinyl) {
          vinyl.style.animationDuration = '4s';
          setTimeout(() => { vinyl.style.animationDuration = '16s'; }, 3000);
        }
      });
    }
  });

  // Initialize track
  loadTrack(0);

  // Cleanup on unload to prevent background timer leaks
  window.addEventListener('beforeunload', () => {
    if (progressInterval) clearInterval(progressInterval);
  });

  // --- SUBMIT FORM FEEDBACK ---
  const submitForm = document.getElementById('submitForm');
  if (submitForm) {
    submitForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const submitBtn = submitForm.querySelector('button[type="submit"]');
      if (!submitBtn) return;
      const origText = submitBtn.innerHTML;

      submitBtn.innerHTML = '<i class="fas fa-check-circle"></i> Submitted! Only Winners Win!';
      submitBtn.style.background = '#28a745';
      submitForm.reset();

      setTimeout(() => {
        submitBtn.innerHTML = origText;
        submitBtn.style.background = '';
      }, 4000);
    });
  }

  // --- INTELLIGENT VIEWPORT-AWARE VIDEO LOOP PLAYBACK ---
  // Saves GPU memory, prevents decoder saturation, and conserves battery by only playing visible videos
  const videoElements = document.querySelectorAll('video');
  if ('IntersectionObserver' in window && videoElements.length > 0) {
    const videoObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        const vid = entry.target;
        if (entry.isIntersecting) {
          const playPromise = vid.play();
          if (playPromise !== undefined) {
            playPromise.catch(() => {
              // Browser autoplay policy or pending load; handled gracefully
            });
          }
        } else {
          vid.pause();
        }
      });
    }, { threshold: 0.15 });

    videoElements.forEach((vid) => {
      vid.addEventListener('error', () => {
        vid.style.display = 'none';
      });
      videoObserver.observe(vid);
    });
  } else {
    videoElements.forEach((vid) => {
      vid.addEventListener('error', () => {
        vid.style.display = 'none';
      });
    });
  }

});
