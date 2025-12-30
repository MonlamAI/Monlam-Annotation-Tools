/**
 * Enhanced Audio Loop Patch for Speech-to-Text Projects
 * 
 * Features:
 * - Auto-loop by default
 * - Toggle button to enable/disable loop
 * - Remember user preference
 * - Visual indicator for loop status
 * - Keyboard shortcut (L key) to toggle
 * 
 * Author: Monlam AI
 * Date: December 30, 2025
 */

(function() {
    'use strict';
    
    console.log('[Monlam] Enhanced Audio Loop Patch loaded');
    
    // User preference (stored in localStorage)
    const STORAGE_KEY = 'monlam_audio_loop_enabled';
    let loopEnabled = localStorage.getItem(STORAGE_KEY) !== 'false'; // Default: true
    
    /**
     * Get or create loop toggle button
     */
    function getOrCreateLoopButton(audioElement) {
        const audioParent = audioElement.parentElement;
        if (!audioParent) return null;
        
        // Check if button already exists
        let button = audioParent.querySelector('.monlam-loop-toggle');
        if (button) return button;
        
        // Create new button
        button = document.createElement('button');
        button.className = 'monlam-loop-toggle';
        button.innerHTML = loopEnabled ? '🔁 Loop ON' : '🔁 Loop OFF';
        button.title = 'Toggle audio loop (Keyboard: L)';
        button.style.cssText = `
            margin-left: 10px;
            padding: 5px 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background: ${loopEnabled ? '#4CAF50' : '#f0f0f0'};
            color: ${loopEnabled ? 'white' : '#333'};
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
        `;
        
        // Add click handler
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleLoop();
        });
        
        // Insert after audio element
        audioElement.parentNode.insertBefore(button, audioElement.nextSibling);
        
        return button;
    }
    
    /**
     * Update loop button appearance
     */
    function updateLoopButton(button) {
        if (!button) return;
        
        button.innerHTML = loopEnabled ? '🔁 Loop ON' : '🔁 Loop OFF';
        button.style.background = loopEnabled ? '#4CAF50' : '#f0f0f0';
        button.style.color = loopEnabled ? 'white' : '#333';
    }
    
    /**
     * Enable/disable looping on an audio element
     */
    function setAudioLoop(audioElement, enabled) {
        if (!audioElement) return;
        
        audioElement.loop = enabled;
        
        // Add visual indicator
        if (enabled) {
            audioElement.style.boxShadow = '0 0 5px rgba(76, 175, 80, 0.5)';
            audioElement.setAttribute('data-loop-enabled', 'true');
        } else {
            audioElement.style.boxShadow = '';
            audioElement.removeAttribute('data-loop-enabled');
        }
        
        // Update or create button
        const button = getOrCreateLoopButton(audioElement);
        updateLoopButton(button);
        
        console.log(`[Monlam] Audio loop ${enabled ? 'enabled' : 'disabled'}:`, audioElement.src);
    }
    
    /**
     * Toggle loop for all audio elements
     */
    function toggleLoop() {
        loopEnabled = !loopEnabled;
        localStorage.setItem(STORAGE_KEY, loopEnabled.toString());
        
        // Apply to all audio elements
        const audioElements = document.querySelectorAll('audio');
        audioElements.forEach(audio => setAudioLoop(audio, loopEnabled));
        
        // Update all buttons
        const buttons = document.querySelectorAll('.monlam-loop-toggle');
        buttons.forEach(updateLoopButton);
        
        console.log(`[Monlam] Audio loop globally ${loopEnabled ? 'enabled' : 'disabled'}`);
        
        // Show toast notification
        showNotification(`Audio loop ${loopEnabled ? 'enabled' : 'disabled'}`);
    }
    
    /**
     * Show toast notification
     */
    function showNotification(message) {
        // Remove existing notification
        const existing = document.querySelector('.monlam-loop-notification');
        if (existing) existing.remove();
        
        const notification = document.createElement('div');
        notification.className = 'monlam-loop-notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #333;
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            font-size: 14px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        // Add animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(notification);
        
        // Auto-remove after 2 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }
    
    /**
     * Apply loop to all existing audio elements
     */
    function applyLoopToExistingAudio() {
        const audioElements = document.querySelectorAll('audio');
        audioElements.forEach(audio => {
            if (!audio.hasAttribute('data-loop-patched')) {
                setAudioLoop(audio, loopEnabled);
                audio.setAttribute('data-loop-patched', 'true');
            }
        });
        
        if (audioElements.length > 0) {
            console.log(`[Monlam] Applied loop to ${audioElements.length} audio elements`);
        }
    }
    
    /**
     * Watch for new audio elements being added to the DOM
     */
    function watchForNewAudio() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) {
                        if (node.tagName === 'AUDIO') {
                            setAudioLoop(node, loopEnabled);
                            node.setAttribute('data-loop-patched', 'true');
                        }
                        const audioElements = node.querySelectorAll && node.querySelectorAll('audio');
                        if (audioElements) {
                            audioElements.forEach(audio => {
                                if (!audio.hasAttribute('data-loop-patched')) {
                                    setAudioLoop(audio, loopEnabled);
                                    audio.setAttribute('data-loop-patched', 'true');
                                }
                            });
                        }
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('[Monlam] Audio observer started');
    }
    
    /**
     * Add keyboard shortcut (L key) to toggle loop
     */
    function addKeyboardShortcut() {
        document.addEventListener('keydown', function(e) {
            // L key (without modifiers)
            if (e.key === 'l' || e.key === 'L') {
                // Don't trigger if typing in input/textarea
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    return;
                }
                
                e.preventDefault();
                toggleLoop();
            }
        });
        
        console.log('[Monlam] Keyboard shortcut registered (L key)');
    }
    
    /**
     * Add loop status indicator to page
     */
    function addStatusIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'monlam-loop-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: ${loopEnabled ? '#4CAF50' : '#999'};
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 9999;
            cursor: pointer;
            transition: all 0.3s ease;
        `;
        indicator.innerHTML = `🔁 Loop: ${loopEnabled ? 'ON' : 'OFF'} <span style="opacity: 0.7">(Press L)</span>`;
        indicator.title = 'Click to toggle audio loop';
        
        indicator.addEventListener('click', toggleLoop);
        
        document.body.appendChild(indicator);
        
        // Update indicator when loop status changes
        window.addEventListener('storage', function(e) {
            if (e.key === STORAGE_KEY) {
                loopEnabled = e.newValue !== 'false';
                indicator.style.background = loopEnabled ? '#4CAF50' : '#999';
                indicator.innerHTML = `🔁 Loop: ${loopEnabled ? 'ON' : 'OFF'} <span style="opacity: 0.7">(Press L)</span>`;
                applyLoopToExistingAudio();
            }
        });
    }
    
    /**
     * Initialize the patch
     */
    function init() {
        console.log('[Monlam] Initializing Enhanced Audio Loop Patch...');
        
        // Apply to existing audio elements
        applyLoopToExistingAudio();
        
        // Watch for new audio elements
        watchForNewAudio();
        
        // Add keyboard shortcut
        addKeyboardShortcut();
        
        // Add status indicator
        addStatusIndicator();
        
        // Check periodically (fallback for dynamic content)
        setInterval(applyLoopToExistingAudio, 3000);
        
        console.log('[Monlam] Enhanced Audio Loop Patch initialized');
        console.log(`[Monlam] Loop is currently ${loopEnabled ? 'ENABLED' : 'DISABLED'}`);
        console.log('[Monlam] Press L key to toggle loop');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Also initialize on page load (for SPAs)
    window.addEventListener('load', function() {
        setTimeout(init, 500); // Small delay for SPA routing
    });
    
    // Expose API for manual control
    window.MonlamAudioLoop = {
        enabled: function() { return loopEnabled; },
        toggle: toggleLoop,
        enable: function() { 
            if (!loopEnabled) toggleLoop(); 
        },
        disable: function() { 
            if (loopEnabled) toggleLoop(); 
        },
        applyToAll: applyLoopToExistingAudio,
        version: '2.0.0'
    };
    
})();

