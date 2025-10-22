# Task 2: AI-Assisted System Design

## Background
Ask Bosco needs a robust architecture for its marketing analytics platform. The current system is starting to show limitations as the company scales. You need to design a next-generation architecture that can handle growth while maintaining reliability and cost-efficiency.

## The Challenge: AI-First Approach
Design a scalable, reliable system for a marketing analytics platform that ingests data from multiple sources, transforms it, applies AI/ML models, and serves insights to clients.

**The twist:** You MUST use AI to help generate the architecture, then improve it with your judgment and business context.

## Requirements
Design a system that can:
- **Ingest data** from 100+ diverse sources (Google Ads, Facebook Ads, GA4, Shopify, TikTok, etc.)
- **Handle scale:** 50,000+ API calls per day, 1TB+ of new data monthly
- **Transform data** to create unified marketing metrics across platforms
- **Support AI/ML:** Apply predictive models for campaign optimization
- **Serve analytics** through real-time dashboards and APIs
- **Ensure data quality:** Validation, monitoring, and alerting
- **Maintain 99.9% availability**
- **Cost-efficient** operation (clients expect margins)
- **Audit & lineage:** Track data provenance for compliance

## Expected Deliverables

Create a file called `TASK2_ARCHITECTURE.md` with:

### Part 1: AI-Generated Architecture (15 minutes)
1. **Use AI to generate initial design:**
   - Use Claude, ChatGPT, or any AI tool
   - Ask it to create a system architecture diagram and explanation
   - Document which AI tool and what prompts you used

2. **Include AI's output:**
   - Architecture diagram (AI-generated or tool-assisted)
   - AI's written explanation

### Part 2: Your Critical Improvements (15 minutes)
3. **Critique and improve AI's design:**
   - What did AI get wrong or miss?
   - What business context did AI lack? (team size, budget, timeline)
   - What assumptions did AI make that don't fit our reality?
   - Where would AI's architecture fail at scale?

4. **Your revised architecture:**
   - Updated diagram with your changes
   - Explanation of key improvements
   - Technology choices with business justification
   - Incremental rollout plan (MVP → Phase 2 → Phase 3)
   - Risk mitigation strategies AI didn't consider

## Constraints
- The company primarily uses **Google Cloud Platform** (but feel free to suggest alternatives)
- The development team has **5 engineers** with varying experience levels
- Marketing agencies are your clients - they expect **reliable, timely data** (their clients depend on it)
- **Cost is important** but reliability is the priority
- Must comply with **GDPR and data protection regulations**

## Special Considerations
1. **Data source variety:** Each platform has different APIs, rate limits, schemas, and reliability
2. **Schema evolution:** Marketing platforms change their APIs regularly
3. **Client customization:** Different clients need different metrics and data sources
4. **Peak loads:** Campaign launches can cause 10x spikes in data volume
5. **Time sensitivity:** Clients need "yesterday's" data available by 8am

## Time
You should spend approximately 30 minutes total on this task.

## What We're Looking For

This is an **AI-era assessment**. We're NOT testing "can you design systems without AI." We're testing:

- **Critical validation:** Can you spot where AI's architecture would fail in production?
- **Business context:** Can you add constraints AI doesn't know? (5-person team, $50K/month budget, 3-month timeline)
- **Pragmatic judgment:** Can you simplify AI's over-engineered solution OR add missing resilience?
- **Team-aware design:** Can you design for a small team that uses AI tools, not a 50-person engineering org?
- **Strategic thinking:** Can you see what to build first vs. what AI suggested to build first?
- **Cost consciousness:** Can you catch when AI suggests expensive solutions without considering margins?

**What great answers include:**
- Clear documentation of what AI suggested and why you changed it
- Business justification for architectural decisions
- Honest assessment of AI's blind spots
- Incremental approach that considers team capacity
- Specific examples of "AI said X, but I chose Y because..."

Remember: VP Engineering in 2025+ means you **use AI to 10x your productivity** while adding the **judgment and context AI lacks**.

