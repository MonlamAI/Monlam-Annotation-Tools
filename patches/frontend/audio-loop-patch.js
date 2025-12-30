/**
 * Audio Loop Patch for Speech-to-Text Projects
 * 
 * This patch makes audio players in STT projects loop by default
 * while keeping all existing controls (play, stop, etc.)
 * 
 * Author: Monlam AI
 * Date: December 30, 2025
 */

(function() {
    'use strict';
    
    console.log('[Monlam] Audio Loop Patch loaded');
    
    /**
     * Enable looping on an audio element
     */
    function enableAudioLoop(audioElement) {
        if (audioElement && !audioElement.hasAttribute('data-loop-patched')) {
            audioElement.loop = true;
            audioElement.setAttribute('data-loop-patched', 'true');
            console.log('[Monlam] Audio loop enabled:', audioElement.src);
        }
    }
    
    /**
     * Apply loop to all existing audio elements
     */
    function applyLoopToExistingAudio() {
        const audioElements = document.querySelectorAll('audio');
        audioElements.forEach(enableAudioLoop);
        console.log(`[Monlam] Applied loop to ${audioElements.length} audio elements`);
    }
    
    /**
     * Watch for new audio elements being added to the DOM
     */
    function watchForNewAudio() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                // Check added nodes
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // Check if the node itself is an audio element
                        if (node.tagName === 'AUDIO') {
                            enableAudioLoop(node);
                        }
                        // Check if the node contains audio elements
                        const audioElements = node.querySelectorAll && node.querySelectorAll('audio');
                        if (audioElements) {
                            audioElements.forEach(enableAudioLoop);
                        }
                    }
                });
            });
        });
        
        // Start observing
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('[Monlam] Audio observer started');
    }
    
    /**
     * Initialize the patch
     */
    function init() {
        // Apply to existing audio elements
        applyLoopToExistingAudio();
        
        // Watch for new audio elements
        watchForNewAudio();
        
        // Also check periodically (fallback)
        setInterval(applyLoopToExistingAudio, 2000);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Also initialize on page load (for SPAs)
    window.addEventListener('load', init);
    
    // Expose functions for manual control if needed
    window.MonlamAudioPatch = {
        enableLoop: enableAudioLoop,
        applyToAll: applyLoopToExistingAudio,
        version: '1.0.0'
    };
    
})();

