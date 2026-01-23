#!/bin/bash
# Patch ToolbarLaptop.vue to add ButtonDefect component
# This script patches the ToolbarLaptop.vue file to include the defect button

TOOLBAR_FILE="$1"

if [ ! -f "$TOOLBAR_FILE" ]; then
    echo "Error: ToolbarLaptop.vue not found at $TOOLBAR_FILE"
    exit 1
fi

echo "Patching ToolbarLaptop.vue to add ButtonDefect component..."

# Check if already patched
if grep -q "ButtonDefect" "$TOOLBAR_FILE"; then
    echo "ToolbarLaptop.vue already contains ButtonDefect, skipping patch"
    exit 0
fi

# 1. Add import statement (after ButtonKeyboardShortcut import)
sed -i '/import ButtonKeyboardShortcut from/a\
import ButtonDefect from '\''./buttons/ButtonDefect.vue'\''
' "$TOOLBAR_FILE"

# 2. Add to components object (after ButtonKeyboardShortcut)
sed -i '/ButtonKeyboardShortcut,/a\
    ButtonDefect,
' "$TOOLBAR_FILE"

# 3. Add projectId computed property (after orderOption)
sed -i '/orderOption(): string {/,/},/{
    /},/a\
    projectId(): number {\
      // @ts-ignore\
      return parseInt(this.$route.params.id, 10)\
    }
}' "$TOOLBAR_FILE"

# 4. Add button-defect to template (after keyboard shortcut button)
sed -i '/<button-keyboard-shortcut/,/<\/v-dialog>/{
    /<\/v-dialog>/a\
\
        <button-defect \
          :project-id="projectId" \
          :example-id="docId" \
        />
}' "$TOOLBAR_FILE"

echo "✅ Successfully patched ToolbarLaptop.vue"

