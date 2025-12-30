#!/bin/bash
# Inject JavaScript inline into index.html and 200.html
# This avoids static file path issues entirely

# Create the inline script block
cat > /tmp/inline-scripts.html << 'EOFSCRIPT'
  <!-- Monlam Enhancements - Inline -->
  <script>
    // Load scripts dynamically to avoid static path issues
    (function() {
      const scripts = [
        '/static/_nuxt/audio-loop-enhanced.js',
        '/static/_nuxt/enhance-members-progress.js',
        '/static/_nuxt/dataset-completion-columns.js'
      ];
      
      scripts.forEach(src => {
        const script = document.createElement('script');
        script.src = src;
        script.onerror = function() {
          console.warn('[Monlam] Could not load:', src);
        };
        document.body.appendChild(script);
      });
    })();
  </script>
EOFSCRIPT

# Inject into index.html
sed -i 's|</body>|'"$(cat /tmp/inline-scripts.html)"'\n</body>|' /doccano/backend/client/dist/index.html

# Inject into 200.html
sed -i 's|</body>|'"$(cat /tmp/inline-scripts.html)"'\n</body>|' /doccano/backend/client/dist/200.html

# Clean up
rm /tmp/inline-scripts.html

