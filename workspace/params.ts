// The values an admin may change in the app without a push: each has a type, a label and a default.
// Written by volty pull. The values admins set stay in the app; an inbox's own params are in its inbox.ts.
import { defineParams } from '~/params'

export default defineParams({
  agencyName: {
    type: 'text',
    label: 'Agency name',
    default: 'Brightwave Digital',
    sensitivity: 'public',
  },
  minRetainerUsd: {
    type: 'number',
    label: 'Minimum monthly fee (USD) for a qualified lead',
    default: 1500,
    help: 'Below this a lead is tier D (not a fit) and gets the free resources instead.',
    sensitivity: 'public',
  },
  hotLeadUsd: {
    type: 'number',
    label: 'Monthly fee (USD) that makes a lead tier A',
    default: 5000,
    help: 'At or above this, with a start within 3 months, the lead goes straight to a strategist.',
    sensitivity: 'public',
  },
  bookingLink: {
    type: 'text',
    label: 'Discovery call booking link',
    default: 'https://brightwave.example/book',
    sensitivity: 'public',
  },
  freeResourcesLink: {
    type: 'text',
    label: 'Free resources link for leads who are not a fit yet',
    default: 'https://brightwave.example/resources',
    sensitivity: 'public',
  },
})
