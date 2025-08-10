# Phase 9.C Archive - Home vs Intake Routing Fix

## Pre-Change State
- Current "/" route renders consumer_templates/index.html (pancake intake)
- Current "/intake" route also renders consumer_templates/index.html (same pancake)
- "/new-request" route renders consumer_templates/consumer_intake_updated.html
- Brand links may point to various routes
- Need to separate home page from intake functionality

## Changes Applied
1. Create proper home landing page at /
2. Route /intake to consumer_intake_updated.html (last-night pancake)
3. Fix navbar brand links to point to /
4. Update all "New Request" links to point to /intake
5. Clean up legacy redirects
6. Archive duplicate templates

Date: 2025-08-10
Phase: 9.C