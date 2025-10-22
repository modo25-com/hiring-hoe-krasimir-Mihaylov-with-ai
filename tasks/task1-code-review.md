# Task 1: AI-Assisted Code Review

## Background
The Marketing Data Service is responsible for aggregating campaign performance data from multiple marketing platforms (Google Ads, Facebook Ads, etc.) and making it available for analytics. The current implementation has several issues that could affect reliability, scalability, and maintenance.

## Task: Two-Phase Approach

### Phase 1: AI-Assisted Review (15 minutes)
1. **Use AI to analyze** `src/services/marketingDataService.py`
   - Use Claude, ChatGPT, Cursor, or any AI tool you prefer
   - Ask it to identify issues with the code
   - Have it suggest fixes for the top 3 issues

2. **Document AI usage:**
   - Which AI tool(s) did you use?
   - What prompt(s) did you give it?
   - What did the AI identify?

### Phase 2: Critical Validation (15 minutes)
3. **Critique the AI's analysis:**
   - Did AI miss any critical issues? What and why?
   - Did AI suggest bad fixes? Which ones and why are they problematic?
   - What business context did AI lack that changed your assessment?
   - What would YOU prioritize differently than the AI?

4. **Your final judgment:**
   - Rank the top 5 issues by priority (with your reasoning)
   - Which fixes would you implement immediately vs. defer?
   - What would you ask your team to address in follow-up work?

## Deliverable
Create a file called `TASK1_ANALYSIS.md` with:
1. **AI Analysis Section:**
   - AI tool(s) used and prompts given
   - AI's findings (copy/paste or screenshot)

2. **Your Critical Review:**
   - Issues AI missed (and why AI missed them)
   - Bad AI suggestions (and what's wrong with them)
   - Business context AI lacked

3. **Your Final Prioritized List:**
   - Top 5 issues with business impact justification
   - What to fix now vs. later (with timeline)
   - Follow-up work for the team

## Time
You should spend approximately 30 minutes total on this task.

## Categories of Issues to Consider
- **Concurrency & Race Conditions:** How does the code handle concurrent requests?
- **Error Handling:** What happens when external APIs fail? Are errors properly logged?
- **Data Quality:** How does the service ensure data integrity and validation?
- **Performance & Scalability:** Will this work at scale? Are there N+1 query issues?
- **Security:** How are credentials handled? Is there input sanitization?
- **Monitoring & Observability:** Can you debug issues in production?
- **Code Quality:** Is the code maintainable? Are there code smells?

## Context for Prioritization
- This service processes data for 50+ active clients
- It runs every hour to sync campaign data
- Failures can cause dashboards to show stale data
- The team consists of 5 engineers (2 data engineers, 1 data scientist, 2 full-stack developers)
- You have 2 weeks until a major client demo

## What We're Looking For

This is an **AI-era assessment**. We're NOT testing "can you code without AI." We're testing:

- **Critical thinking:** Can you catch what AI missed or got wrong?
- **Business judgment:** Can you add context AI doesn't have (customer impact, team capacity, timeline)?
- **Prioritization:** Can you make strategic calls beyond what AI suggests?
- **Validation skills:** Can you explain WHY AI suggestions are good or bad?
- **Leadership:** How do you balance AI recommendations with business reality?

Remember: VP Engineering in 2025+ means you **validate AI output** and **make judgment calls AI cannot** - not that you code everything from scratch.

