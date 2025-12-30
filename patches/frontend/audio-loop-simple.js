/**
 * Simple Audio Loop - Auto-loop audio without UI
 * Silently enables loop on all audio elements
 */

(function() {
    'use strict';
    
    console.log('[Monlam] Simple Audio Loop Patch loaded');
    
    /**
     * Apply loop and auto-play to audio element
     */
    function applyLoop(audio) {
        if (!audio.hasAttribute('data-loop-applied')) {
            audio.loop = true;
            audio.setAttribute('data-loop-applied', 'true');
            
            // Auto-play the audio
            if (audio.readyState >= 2) {
                // Audio is loaded, try to play
                playAudio(audio);
            } else {
                // Wait for audio to load
                audio.addEventListener('canplay', () => playAudio(audio), { once: true });
            }
            
            console.log('[Monlam] Loop and auto-play applied to audio:', audio.src);
        }
    }
    
    /**
     * Attempt to play audio (handles browser autoplay restrictions)
     */
    function playAudio(audio) {
        const playPromise = audio.play();
        
        if (playPromise !== undefined) {
            playPromise
                .then(() => {
                    console.log('[Monlam] Audio auto-playing successfully');
                })
                .catch(error => {
                    // Browser blocked autoplay (common with audio)
                    console.log('[Monlam] Autoplay blocked, waiting for user interaction:', error.message);
                    
                    // Add one-time click listener to start playback
                    const startPlayback = () => {
                        audio.play();
                        document.removeEventListener('click', startPlayback);
                        console.log('[Monlam] Audio started after user interaction');
                    };
                    document.addEventListener('click', startPlayback, { once: true });
                });
        }
    }
    
    /**
     * Apply to all existing audio elements
     */
    function applyToAll() {
        const audioElements = document.querySelectorAll('audio');
        audioElements.forEach(applyLoop);
        
        if (audioElements.length > 0) {
            console.log(`[Monlam] Applied loop to ${audioElements.length} audio elements`);
        }
    }
    
    /**
     * Watch for new audio elements
     */
    function watchForNewAudio() {
        const observer = new MutationObserver(function() {
            applyToAll();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    /**
     * Initialize
     */
    function init() {
        // Apply to existing audio
        applyToAll();
        
        // Watch for new audio
        watchForNewAudio();
        
        // Re-apply periodically (in case Vue recreates elements)
        setInterval(applyToAll, 1000);
        
        console.log('[Monlam] Audio loop initialized (silent mode)');
    }
    
    // Wait for page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

