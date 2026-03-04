# Requirement Doc Drafter — Project Context

## What we're building
An n8n workflow + Claude prompt that turns messy discovery session inputs into a structured PRD with Epics and User Stories.

## Inputs
- Meeting transcripts (Teams, Otter, Fireflies etc.)
- Typed notes from during the meeting
- Both / either — workflow should handle both

## Output format
- Full PRD template
- Epics embedded in the PRD
- User Stories embedded under each Epic
- Plain text for now → Confluence / Notion integration later

## PRD Template sections (to build)
1. Document Info (title, date, author, version, client, status)
2. Problem Statement — what problem are we solving and for whom
3. Goals & Success Metrics — what does good look like
4. Scope — what's in, what's out
5. Assumptions & Constraints
6. Stakeholders
7. Epics & User Stories — structured as:
   - Epic: [name]
   - User Story: As a [persona], I want [action], so that [benefit]
   - Acceptance Criteria per story
8. Open Questions — things that need answers before work can start
9. FS / Regulatory Considerations — flag anything relevant (FCA, GDPR, data sensitivity, audit trail etc.)

## FS knowledge layer
- Flag regulatory considerations where relevant (FCA, PRA, GDPR, Consumer Duty, DORA etc.)
- Note data sensitivity / classification issues
- Flag audit/compliance trail requirements
- Keep it contextual — only surface if genuinely relevant

## Tech stack
- n8n for workflow orchestration
- Claude (claude-sonnet-4-6) for the AI step
- Plain text output for now
- Future: Confluence / Notion output

## Status
- [ ] Design Claude prompt
- [ ] Design n8n workflow
- [ ] Test with sample transcript
- [ ] Add Confluence/Notion output
