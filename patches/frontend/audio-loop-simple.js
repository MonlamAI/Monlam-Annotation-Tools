/**
 * Simple Audio Loop - Auto-loop audio without UI
 * Silently enables loop on all audio elements
 */

(function() {
    'use strict';
    
    console.log('[Monlam] Simple Audio Loop Patch loaded');
    
    /**
     * Apply loop to audio element
     */
    function applyLoop(audio) {
        if (!audio.hasAttribute('data-loop-applied')) {
            audio.loop = true;
            audio.setAttribute('data-loop-applied', 'true');
            console.log('[Monlam] Loop applied to audio:', audio.src);
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

