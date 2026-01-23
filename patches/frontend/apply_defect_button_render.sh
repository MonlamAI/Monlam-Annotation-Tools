#!/bin/bash
# Script to apply ButtonDefect component changes on Render
# Run this via Render Shell after deployment

echo "Applying Defect Button patch to Render deployment..."

# Find ToolbarLaptop.vue in the compiled dist
TOOLBAR_PATHS=(
    "/doccano/backend/client/dist/components/tasks/toolbar/ToolbarLaptop.vue"
    "/doccano/backend/staticfiles/components/tasks/toolbar/ToolbarLaptop.vue"
    "/doccano/frontend/components/tasks/toolbar/ToolbarLaptop.vue"
)

TOOLBAR_FILE=""
for path in "${TOOLBAR_PATHS[@]}"; do
    if [ -f "$path" ]; then
        TOOLBAR_FILE="$path"
        echo "Found ToolbarLaptop.vue at: $path"
        break
    fi
done

if [ -z "$TOOLBAR_FILE" ]; then
    echo "⚠️  ToolbarLaptop.vue not found in expected locations"
    echo "This is normal - Vue components are compiled to JavaScript"
    echo "The defect button will be added via JavaScript injection instead"
    exit 0
fi

# If source file exists, patch it
if [ -n "$TOOLBAR_FILE" ]; then
    echo "Patching $TOOLBAR_FILE..."
    
    # Check if already patched
    if grep -q "ButtonDefect" "$TOOLBAR_FILE"; then
        echo "✅ Already patched"
        exit 0
    fi
    
    # Apply patch using sed
    sed -i '/import ButtonKeyboardShortcut/a\
import ButtonDefect from '\''./buttons/ButtonDefect.vue'\''
' "$TOOLBAR_FILE"
    
    sed -i '/ButtonKeyboardShortcut,/a\
    ButtonDefect,
' "$TOOLBAR_FILE"
    
    sed -i '/orderOption(): string {/,/},/{
        /},/a\
    projectId(): number {\
      return parseInt(this.$route.params.id, 10)\
    }
}' "$TOOLBAR_FILE"
    
    sed -i '/<button-keyboard-shortcut/,/<\/v-dialog>/{
        /<\/v-dialog>/a\
\
        <button-defect \
          :project-id="projectId" \
          :example-id="docId" \
        />
}' "$TOOLBAR_FILE"
    
    echo "✅ Patched successfully"
fi

