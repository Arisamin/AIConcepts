# Leumit Login State Detection Workflow

This document describes the workflow for detecting whether you are logged in to the Leumit website, as used by the automation agent.

## Workflow Steps

1. **Navigate to google.com.**
2. **Search for "לאומית".**
3. **Click on the Leumit link in the search results.**
4. **On the Leumit homepage:**
   - If the button labeled **"איזור אישי"** (Personal Area) is present:
     - You are **NOT** logged in.
     - Proceed with the login procedure.
   - Else, if the button labeled **"זימון תורים"** (Appointment Scheduling) is present:
     - You **ARE** logged in.
     - Continue with the workflow (no login needed).
   - If neither button is found:
     - Trigger the retry login mechanism (handle as an error or unexpected state).

## Notes
- This logic is the main guideline for robust login state detection in the agent.
- The workflow ensures the agent only attempts login when necessary and can recover from unexpected states.
