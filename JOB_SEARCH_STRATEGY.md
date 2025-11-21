# Job Search Strategy - ML Engineer Role

**Target Salary**: ₹25-50L/year
**Timeline**: 30-60 days to interviews
**Primary Value Prop**: Production ML system builder with honest approach to failure

---

## Phase 1: Portfolio Preparation (Days 1-7)

### Day 1-2: GitHub Portfolio
- [ ] Create public GitHub repository
- [ ] Upload full codebase (with sensitive data removed)
- [ ] Add comprehensive README (already done)
- [ ] Add LICENSE file (MIT)
- [ ] Create .gitignore (exclude .env, databases with real data)
- [ ] Tag release: v1.0.0-validated

### Day 3-4: LinkedIn Optimization
- [ ] Update headline: "ML Engineer | Built Production Trading System (Failed but Learned)"
- [ ] Add project to Experience section
- [ ] Write LinkedIn post (see LINKEDIN_POST_DRAFT.md)
- [ ] Add skills: FastAPI, XGBoost, Multi-Agent AI, AWS, Python
- [ ] Get 3-5 endorsements from connections

### Day 5-7: Portfolio Website (Optional)
- [ ] Create simple site with project showcase
- [ ] Include: Architecture diagram, code samples, validation results
- [ ] Link to GitHub and LinkedIn
- [ ] Deploy to Vercel/Netlify (free)

---

## Phase 2: Job Application (Days 8-30)

### Target Companies

**Tier 1: Trading Firms/Hedge Funds** (₹40-60L)
- Quadeye
- Graviton Research Capital
- Tower Research Capital
- WorldQuant
- Two Sigma (India)

**Tier 2: Fintech** (₹30-50L)
- Zerodha
- Groww
- Upstox
- PayTM Money
- INDmoney

**Tier 3: ML/AI Companies** (₹25-40L)
- Fractal Analytics
- Tiger Analytics
- LatentView Analytics
- Mu Sigma
- Genpact AI

**Tier 4: Product Companies** (₹25-45L)
- Google India (ML Engineer)
- Amazon (Applied Scientist)
- Microsoft (ML Engineer)
- Flipkart (ML Engineer)
- PhonePe

### Application Strategy

**Week 2** (Days 8-14):
- Apply to 10 companies (mix of all tiers)
- Customize cover letter for each
- Mention project in application

**Week 3-4** (Days 15-30):
- Follow up on applications
- Apply to 10 more companies
- Network on LinkedIn (connect with ML engineers at target companies)

---

## Phase 3: Interview Preparation (Days 8-60)

### Technical Prep

**ML Fundamentals** (Daily: 2 hours):
- Review: Supervised learning, classification, regression
- Practice: XGBoost, LightGBM, random forests
- Metrics: Precision, recall, F1, ROC-AUC
- Feature engineering best practices
- Model deployment patterns

**Coding** (Daily: 1 hour):
- LeetCode: 50 medium problems (focus on arrays, strings, trees)
- System design: ML system design (model serving, feature stores)

**ML System Design** (Weekly: Review these):
- Design fraud detection system
- Design recommendation engine
- Design real-time prediction API
- Design feature engineering pipeline

### Behavioral Prep

**Your Story** (Memorize this):
> "I spent 3 months building a production ML system to test if earnings quality predicts stock movements. I built the complete infrastructure - multi-agent orchestration, feature engineering, AWS deployment, FastAPI service.
>
> The hypothesis failed: 38% win rate vs 60% target. But this taught me critical lessons about validating assumptions early, prioritizing data quality, and knowing when to pivot.
>
> I'm looking for opportunities where I can apply these skills to validated problems at [Company Name]."

**STAR Stories** (Prepare 5):
1. **Technical Challenge**: Building multi-agent orchestration system
2. **Failure & Learning**: Hypothesis invalidation and lessons learned
3. **System Design**: FastAPI prediction API with <100ms latency
4. **Data Quality**: Dealing with 20% bad data from PDF extraction
5. **Independence**: Self-driven 3-month solo project

---

## Interview Talking Points

### When Asked "Tell Me About Your Project"

**Answer Structure** (2 minutes):

1. **Problem** (20 seconds):
   "I wanted to test if earnings quality predicts stock price movements in Indian markets."

2. **Solution** (60 seconds):
   "I built a complete ML system: scraped BSE/NSE earnings data, engineered 25+ features, trained XGBoost models, deployed FastAPI service to AWS with systemd integration. The system had multi-agent orchestration for data collection, model registry for versioning, and Telegram alerts for notifications."

3. **Results** (20 seconds):
   "Tested 42 alerts. Win rate: 38% vs 60% target. System doesn't predict profitably."

4. **Learnings** (20 seconds):
   "Key lesson: Validate hypotheses before building infrastructure. I spent 3 months on a technically impressive system that doesn't solve the business problem. Next time: test hypothesis in week 1, then build."

### When Asked "Why Did It Fail?"

**Answer** (honest but insightful):

"Three root causes:

1. **Wrong hypothesis**: Markets are forward-looking. Earnings often priced in before announcement.

2. **Insufficient features**: Only used earnings data. Missed: price patterns, sentiment, sector rotation, technical signals.

3. **Wrong prediction target**: Upper circuits are rare (5-10%). Should have predicted simpler target like '3-day positive return.'

The infrastructure works perfectly. The business logic was flawed. That's the difference between engineering and product-market fit."

### When Asked "What Would You Do Differently?"

**Answer**:

"1. **Week 1**: Simple correlation test (earnings vs price)
2. **Week 2**: If correlation exists, validate on 50 samples
3. **Week 3**: Decision point - continue or pivot
4. **Week 4+**: Only build if hypothesis validated

Total time to validation: 3 weeks instead of 3 months.

This is classic lean startup: build-measure-learn, but I built for 3 months before measuring. Never again."

---

## Networking Strategy

### LinkedIn Outreach (10 messages/week)

**Template**:

> Hi [Name],
>
> I noticed you work as [Role] at [Company]. I recently completed a 3-month project building a production ML trading system (FastAPI, XGBoost, AWS). The trading hypothesis failed (38% win rate vs 60% target), but I learned valuable lessons about hypothesis validation and data quality.
>
> I'm currently looking for ML Engineer opportunities at [Company]. Would you be open to a 15-minute chat about your experience there and any advice for someone with my background?
>
> My project: [GitHub link]
>
> Thanks,
> [Your Name]

### Response Rate Expectations
- 20-30% response rate
- 10 messages → 2-3 responses
- 2-3 responses → 1 referral (if conversation goes well)

---

## Cover Letter Template

**For Trading Firms/Hedge Funds**:

> Dear [Hiring Manager],
>
> I'm writing to apply for the ML Engineer role at [Company]. I recently completed a 3-month project building a production ML trading system that, while failing to predict profitably, demonstrates the end-to-end ML engineering skills needed for this role.
>
> **Technical Highlights**:
> - Built FastAPI prediction service (<100ms latency target)
> - Deployed to AWS with systemd integration and health monitoring
> - Implemented multi-agent orchestration for data collection
> - Engineered 25+ features (technical, financial, sentiment)
> - Created model registry for versioning and A/B testing
>
> **Key Learning**:
> The trading hypothesis failed (38% win rate vs 60% target), teaching me the critical importance of validating assumptions early. This aligns with [Company]'s rigorous, data-driven approach.
>
> I'm excited about the opportunity to apply these skills to [Company]'s validated trading strategies.
>
> Full project: [GitHub link]
>
> Best,
> [Your Name]

---

## Salary Negotiation

### Know Your Worth

**Junior ML Engineer** (0-2 years): ₹15-25L
**Mid-Level ML Engineer** (2-4 years): ₹25-40L
**Senior ML Engineer** (4+ years): ₹40-60L

**Your Position**:
- 0 years industry experience
- BUT: Production system built end-to-end
- Position yourself as: "Junior with senior project experience"
- Target: ₹25-35L (stretching to ₹40L at top firms)

### Negotiation Strategy

1. **Don't give number first**: "I'm looking for fair market rate for this role. What's the budgeted range?"

2. **If pressed**: "Based on my research and the skills demonstrated in my project, I'm targeting ₹30-35L base. But I'm flexible based on total compensation and learning opportunities."

3. **Emphasize**: "While I don't have industry experience, my project demonstrates production ML skills. I'm betting on myself that I can deliver senior-level impact quickly."

---

## 30-Day Action Plan

**Week 1** (Days 1-7):
- [ ] Monday: GitHub repo setup
- [ ] Tuesday: LinkedIn optimization
- [ ] Wednesday: Write 5 STAR stories
- [ ] Thursday: Portfolio website (if doing)
- [ ] Friday-Sunday: Interview prep (ML fundamentals)

**Week 2** (Days 8-14):
- [ ] Monday-Wednesday: Apply to 10 companies
- [ ] Thursday-Friday: LinkedIn networking (10 messages)
- [ ] Weekend: LeetCode practice

**Week 3** (Days 15-21):
- [ ] Monday-Wednesday: Apply to 10 more companies
- [ ] Thursday-Friday: Follow up on Week 2 applications
- [ ] Weekend: ML system design prep

**Week 4** (Days 22-30):
- [ ] Review applications, follow up
- [ ] Continue networking
- [ ] Mock interviews (3-5)
- [ ] Adjust strategy based on responses

---

## Success Metrics

**After 30 days**:
- 20 applications sent
- 20 LinkedIn connections made
- 5-10 responses/referrals
- 2-3 initial screens

**After 60 days**:
- 40 applications sent
- 3-5 final round interviews
- 1-2 offers

---

## Backup Plans

### If No Offers After 60 Days

**Plan B**: Freelance/Contract ML Work
- Upwork, Toptal for ML projects
- Build portfolio while earning
- Revisit full-time search after 3 months

**Plan C**: Sell Infrastructure
- Pitch to algo trading startups (₹5-15L one-time)
- Use proceeds to fund longer job search

**Plan D**: Pivot to Different Role
- Data Engineer (easier to land)
- Backend Engineer (Python/FastAPI skills)
- Use as stepping stone to ML role

---

## Resources

**Job Boards**:
- LinkedIn Jobs
- Naukri.com (India)
- AngelList (startups)
- Instahyre (curated)
- Cutshort (tech roles)

**Networking**:
- LinkedIn
- Twitter (FinTwit, ML Twitter)
- Meetups (Bangalore ML meetups)
- Conferences (PyData, ML conferences)

**Interview Prep**:
- LeetCode (coding)
- ML System Design Interview (book)
- Chip Huyen's ML Interviews Book
- Eugene Yan's blog (applied ML)

---

**Created**: November 18, 2025
**Status**: Ready to Execute
**Next Action**: Create GitHub repository (Day 1)
