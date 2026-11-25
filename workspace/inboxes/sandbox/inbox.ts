// The Sandbox inbox: hours, reply targets, hand-off, priority guide, routing, Volty's reply mode and its web chat.
// Written by volty pull from the live inbox. Who works the inbox, team members and channels stay in the app.
import { defineInbox } from '~/inbox'

export default defineInbox({
  name: "Sandbox",
  icon: {
    kind: "emoji",
    value: "🚧",
  },
  autoEnrollOrgMembers: true,
  businessHours: null,
  idleClose: {
    afterMinutes: 1440,
    owned: false,
  },
  firstResponseMinutes: 5,
  handoff: {
    targetMinutes: 60,
    topics: [
      "Hot lead ready for a strategist (tier A)",
      "Qualified lead to follow up (tier B)",
      "Custom pricing, discount or contract terms",
      "The lead asks to speak to a person",
      "Existing client with an account or billing issue",
      "Complaint, refund or an upset contact",
      "Legal, privacy or data-deletion request",
      "Question the knowledge base cannot answer",
    ],
    tellContact: true,
  },
  priority: {
    smartPriority: "on",
    smartSegments: "off",
    guide: {
      high: "A tier A lead (monthly budget at or above the hot-lead threshold, starting within 3 months), an existing client with a problem, or a complaint.",
      medium: "A tier B lead, or a lead still being qualified who has shared a budget.",
      low: "Tier C or D leads, job seekers, vendor pitches and spam.",
    },
  },
  routing: {
    mode: "rules_only",
    policy: null,
    openCap: null,
    rules: [],
  },
  volty: {
    agent: "Volty",
    defaultResponder: true,
    replyMode: "live",
    afterHoursReplyMode: null,
    window: null,
    liveForNewContacts: false,
    stepBackMinutes: 30,
    newContactWindowDays: null,
    waitExtends: false,
    selfStepDown: null,
  },
  webChat: null,
})
