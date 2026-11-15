const LABELS: Record<string, string> = {
  enquiry_received: 'Enquiry received',
  original_data_saved: 'Original data saved',
  team_assignment: 'Assigned to a team member',
  email_notification: 'Team email alert',
  workflow_started: 'AI workflow started',
  duplicate_detection: 'Duplicate detection',
  ai_analysis: 'AI analysis & information extraction',
  category_classification: 'Category classification',
  priority_assignment: 'Priority assignment',
  sentiment_intent_analysis: 'Sentiment & intent analysis',
  lead_scoring: 'Lead scoring',
  missing_information_detection: 'Missing information detection',
  response_generation: 'Customer response generation',
  followup_suggestions: 'Follow-up suggestions',
  database_update: 'Results saved to database',
  workflow_completed: 'Workflow completed',
  workflow_failed: 'Workflow failed',
}
export const stepLabel = (s: string) => LABELS[s] ?? s.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())

