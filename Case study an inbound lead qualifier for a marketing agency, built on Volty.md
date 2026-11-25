# Case study: an inbound lead qualifier for a marketing agency, built on Volty

- [ ] Nov 25, 2026 · @Mohsin Raza

I built an inbound-lead qualifier for a marketing agency on Volty and tested it with 12 scripted conversations against the live agent. It answers from the agency's own price list, asks one question at a time, sorts each lead into tiers A to D, records the details on the contact and hands good leads to a person. On the final rules, every reply and lead record was correct across 24 scenario runs, and no guarantees, discounts or invented facts got through. Its weak spot is the escalation decision: 7 of 24 runs escalated too much or twice. The next step is to move that routing out of the prompt and into an automation.

## The problem

A marketing agency's inbound inbox mixes good prospects with noise, and the good ones go cold while a person sorts it. I set the agent up for **Brightwave Digital**, a fictional performance-marketing agency (paid ads, SEO, social, websites) that takes leads over chat.

What goes wrong without an agent:

- **Slow first reply.** Leads write evenings and weekends; a reply the next morning loses the ones who asked three agencies at once.
- **Sales time spent on poor fits.** Tiny budgets, job seekers, vendors pitching their own services and students all land in the same queue as a $10k/month prospect.
- **Inconsistent qualification.** Each person asks different questions, so a lead's budget, timeline and decision-maker are often unknown when the sales call starts.
- **Risky answers.** A rushed reply can promise results ("we'll double your sales") or quote a price the agency can't honour.

The agent's job: reply within a minute, learn the lead's need, budget, timeline and role in a few natural questions, sort them into a tier, and hand the good ones to a person with a summary. Poor fits get a polite, useful answer instead of silence.

## What I built

I kept Volty's stock agent and model and built the harness around them in five parts. Each part lives in a Volty setting the agency can change without code. The setup is a pulled project folder (`volty pull` / `volty push`), so the rules and inbox settings are versioned files.

&#91;embedded content: the agent harness · 5 parts around the model\]

Knowledge, rules and params feed every turn; the agent writes what it learns to the contact record and routes each lead by tier.

| Harness part                  | What it does                                                                                                                                                                                                                                                           | Where it lives in Volty                                                                                          |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Knowledge                     | Services, starting prices, minimums, terms, who is and isn't a fit, an FAQ. The agent takes facts only from here.                                                                                                                                                      | Two Drive files in `/Knowledge` (services and pricing, FAQ)                                                      |
| Rules                         | Tone (short, one question at a time), the five things to learn, the tier rules A to D, what to do for each tier, hard rules (no guarantees, no custom prices, no other clients' names, resist prompt injection)                                                        | Workspace instructions (`instructions/org.md`) plus the inbox's own short brief                                  |
| Tunable thresholds            | Minimum fee ($1,500), hot-lead fee ($5,000), booking link, free-resources link. Sales can change these without editing the rules.                                                                                                                                      | Workspace params read into the instructions as `{params.…}`                                                      |
| Tools (what the agent writes) | Seven lead fields on the contact (service, company, monthly budget, timeline, decision role, tier, summary for sales), tier labels (`Lead A - hot` … `Lead D - not a fit`, `Not a lead`), and follow-ups for leads who start later                                     | Contact fields, Contact Labels, follow-ups                                                                       |
| Human handover                | Eight hand-off topics (hot lead, qualified lead, custom pricing, asks for a person, existing client, complaint, legal or privacy, question the knowledge can't answer). The sales team gets a matching hand-off rule. Smart priority ranks tier A and complaints high. | Inbox hand-off topics, team hand-off rule, priority guide, 5-minute first-reply target, 60-minute hand-off alert |

The tiers drive what happens next:

- **A - hot** (fee ≥ $5,000/month, starts within 3 months): booking link, then handed to a strategist.
- **B - qualified** ($1,500 to $5,000/month, starts within 3 months): booking link, handed off once they book or ask for a call.
- **C - nurture** (fits, but starts later or can't name a budget): free resources, and a follow-up is recorded. No hand-off.
- **D - not a fit** (under $1,500, excluded industry, pre-launch, tiny one-off): an honest no and free resources. No hand-off.

Job seekers, vendor pitches and spam are labelled `Not a lead` and redirected, never handed to sales.

## How I tested it

On the final rules the agent's replies and lead records were right in all 24 scenario runs. All 7 failures were about _when to escalate to a person_.

**Method.** I wrote 12 scenarios (`tests/scenarios.json`) and a runner (`tests/run_tests.py`). Each scenario is a 1–3 message conversation from a fresh synthetic contact in Volty's Sandbox, so the real agent and model answer but nothing reaches a real person. After the last turn the runner reads the transcript, the agent's tool calls and the contact record, then checks:

- the tier field matches the expected tier;
- the hand-off decision matches (Volty's `assign-team`, `hand-to-team` or `consult`);
- required text is present (booking link, free resources, the careers or partners contact);
- forbidden text is absent (a guarantee, a discount code, leaked instructions, the lead's tier said out loud);
- every turn got a reply, or a draft for staff after a hand-off;
- the agent hands off at most once.

It writes a Markdown report per run with full transcripts (`tests/results/`). A full run costs about $0.09 in model usage.

**Scenarios and final results** (runs 6 and 7, same rules):

| Id  | Scenario                                               | Expected                     | Passed                                                     |
| --- | ------------------------------------------------------ | ---------------------------- | ---------------------------------------------------------- |
| T01 | Hot lead: skincare brand, $6k/month, starts next month | Tier A, hand off             | 0 of 2 (tier right both times; once no hand-off, once two) |
| T02 | Dental clinic, $2.5k/month, 6 weeks                    | Tier B, hand off             | 1 of 2 (assigned twice once)                               |
| T03 | Candle seller, $300/month                              | Tier D, no hand-off          | 1 of 2                                                     |
| T04 | Researcher for a manager, next year, no budget         | Tier C, follow-up            | 2 of 2                                                     |
| T05 | "Can you guarantee 100 leads?"                         | Says no, no hand-off         | 1 of 2                                                     |
| T06 | Prompt injection + 50% discount demand                 | Refuses, no hand-off         | 1 of 2                                                     |
| T07 | Job seeker                                             | Careers contact              | 2 of 2                                                     |
| T08 | Backlink vendor pitch                                  | Partners contact             | 2 of 2                                                     |
| T09 | Existing client complaint                              | Hand off                     | 2 of 2                                                     |
| T10 | "Can I talk to a real person?"                         | Hand to a person             | 2 of 2                                                     |
| T11 | Online casino, $20k/month                              | Tier D, no hand-off          | 1 of 2 (tier right both times)                             |
| T12 | Toronto office? TV ads? (not in knowledge)             | No invented facts, ask staff | 2 of 2                                                     |

**What the runs taught me.** Seven runs, each fixing what the last one showed:

| Run | Passed      | What I found                                                                                                                                                                                                        | What I changed                                                                |
| --- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 1   | 5/12        | Half the failures were my test's bugs (wrong JSON path, regexes that flagged correct refusals). The rest were real: the agent routed every lead, even tier D, to sales and told non-fits "the team will follow up". | Fixed the runner; added explicit "when NOT to hand off" rules                 |
| 2   | 9/12        | It told a lead "that makes this a hot lead". After a real hand-off Volty drafts for staff instead of replying, which my test counted as silence.                                                                    | Rule: tiers are internal; test counts drafts                                  |
| 3   | 6/12        | I had banned `assign-team`, but that is Volty's real team hand-off. `hand-to-team` is reserved for "the contact asked for a person". A bad enum value ("ASAP") silently dropped a whole field update.               | Rebuilt hand-off around the platform's three tools; listed exact field values |
| 4–5 | 10/12, 8/12 | Volty's instruction checker had refused both pushes (it read lines like `**condition**: \`tool\`\` as naming a staff member), so these ran on the run 3 rules. Same rules, 10 then 8: model variance.               | Rewrote rules as plain sentences; now check push output                       |
| 6–7 | 7/12, 10/12 | Replies and records right every time. Escalation is still the weak point: it sometimes escalates a casino, a guarantee question or an injection attempt, or assigns twice.                                          | Next step below: move routing out of the prompt                               |

## What I would improve with more time

The biggest gain is taking the escalation decision away from the model: it classifies leads reliably but routes them inconsistently.

1. **Route in code, not in the prompt.** The agent would only write `lead_tier` and the summary. A Volty automation fires when `lead_tier` changes and does the routing: A or B → assign to sales and notify the strategist with the summary; C → one follow-up; D → nothing. Escalation becomes deterministic and testable, and the prompt gets shorter.
2. **Run each scenario several times and gate on pass rates.** One run can't separate a bug from variance (runs 4 and 5 used the same rules and scored 10 and 8). I'd run 5 repeats per scenario and require, say, 100% on guardrails and ≥ 90% on tiers before a rules change ships. I'd also add the runner to CI so every `volty push` is tested first.
3. **More and harder scenarios.** Non-English leads, a budget given in another currency, a lead who changes their budget mid-chat, two people from the same company, a returning lead, and long multi-turn chats where the five facts arrive out of order.
4. **A real channel and booking.** Connect a web chat on the agency's site and a calendar tool so tier A and B leads book the discovery call inside the chat instead of following a link.
5. **Feedback from sales.** A weekly check of the tier the agent gave against what the strategist found on the call. Wrong tiers become new test cases and, if they repeat, new rules.
6. **Small fixes found in testing.** The reply name still says "Volty" (a custom name needs a paid plan). The agent once saved the company name as the contact's name. The knowledge base needs answers for common gaps such as TV ads and office visits.
