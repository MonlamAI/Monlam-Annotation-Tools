# Comprehensive Fix Plan

## Problems Identified

### 1. Metrics Page
**Issues:**
- Destroys original Doccano metrics page completely
- Shows on wrong pages due to overly broad URL matching
- Empty data tables (no assignments created yet)
- MutationObserver continues running on all pages

**Fix:**
- Add a dedicated `/completion-matrix` page route instead of hijacking /metrics
- OR: Add as a tab/section WITHIN metrics, not replace it
- Stop MutationObserver after injection
- Show helpful message when no data exists

### 2. Dataset Columns  
**Issues:**
- Script loads but columns don't appear
- Need to verify: Is it waiting for table? Is API working?

**Fix:**
- Add better logging
- Check if table exists before trying to add columns
- Verify API returns data for examples

### 3. Audio Loop
**Issues:**
- Not auto-playing on annotation pages

**Fix:**
- Verify page detection logic
- Check if audio elements exist
- Test autoplay browser restrictions

### 4. Approve/Reject Buttons
**Issues:**
- Not appearing on annotation pages

**Fix:**
- Check role detection
- Verify button injection logic
- Check if toolbar exists

## Industry Best Practices

### 1. Non-Invasive Integration
✅ **DO:** Add features alongside existing ones
❌ **DON'T:** Replace core application content

### 2. Progressive Enhancement
✅ **DO:** Enhance existing pages gracefully
❌ **DON'T:** Hijack entire page rendering

### 3. Defensive Programming
✅ **DO:** Check if elements exist before manipulating
❌ **DON'T:** Assume DOM structure

### 4. Proper Scoping
✅ **DO:** Run scripts only on relevant pages
❌ **DON'T:** Let MutationObservers run everywhere

### 5. Empty State Handling
✅ **DO:** Show helpful messages when no data
❌ **DON'T:** Show empty tables silently

## Recommended Approach

### Option A: Dedicated Completion Matrix Page (RECOMMENDED)
- Create `/projects/{id}/completion` route
- Doesn't interfere with existing metrics
- Clean, dedicated UI
- Requires backend URL registration

### Option B: Metrics Page Enhancement
- Keep original metrics
- Add "Completion Tracking" section below
- Toggle visibility
- Less invasive

### Option C: Metrics Tab
- Add new tab to metrics page
- Switch between "Project Metrics" and "Completion Tracking"
- Best UX, moderate complexity

## Immediate Action Plan

1. **Fix metrics script to NOT destroy page**
   - Check if completion matrix already exists
   - Append, don't replace

2. **Add comprehensive logging**
   - Every script logs its state
   - Easy to debug

3. **Test each feature individually**
   - Isolate what works vs doesn't

4. **Create working demo with dummy data**
   - Populate database with test assignments
   - Verify all features work end-to-end

