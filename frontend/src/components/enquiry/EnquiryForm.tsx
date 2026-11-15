import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Send } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import type { EnquiryCreate } from '@/types/api'

// Mirrors the backend rules (backend/app/utils/validators.py + schemas/enquiry.py) so people get instant feedback.
// The backend still re-validates everything.
const schema = z.object({
  customer_name: z.string().trim().min(1, 'Please enter a name').max(150, 'That name is too long (max 150 characters)'),
  phone: z
    .string()
    .trim()
    .min(1, 'Please enter a phone number')
    .refine((v) => /^\+?\d{7,15}$/.test(v.replace(/[\s\-().]/g, '')), 'Enter a valid phone number (7–15 digits, optional leading +)'),
  email: z.string().trim().min(1, 'Please enter an email address').email('That email address does not look right'),
  message: z.string().trim().min(1, 'Please tell us a little about what you need').max(5000, 'That is too long (max 5000 characters)'),
})
export type EnquiryFormValues = z.infer<typeof schema>

function Field({ label, error, children, htmlFor }: { label: string; error?: string; children: React.ReactNode; htmlFor: string }) {
  return (
    <div>
      <label htmlFor={htmlFor} className="text-sm font-medium text-slate-700">
        {label} <span className="text-clay" aria-hidden>*</span>
      </label>
      <div className="mt-1.5">{children}</div>
      {error && <p role="alert" className="mt-1 text-xs text-red-700">{error}</p>}
    </div>
  )
}

const inputCls = (invalid: boolean) =>
  `w-full rounded-lg border bg-white/75 px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 backdrop-blur focus:outline-none focus:ring-2 ${
    invalid ? 'border-red-400 focus:ring-red-500/20' : 'border-slate-300/80 focus:border-brand-500 focus:ring-brand-500/20'
  }`

interface Props {
  onSubmit: (values: EnquiryCreate) => Promise<void> | void
  submitting: boolean
  serverFieldErrors?: Record<string, string>
  /** value saved in the enquiry's `source` column */
  source?: string
  /** customer-facing wording ("Your name", "How can we help?") instead of admin wording */
  customerFacing?: boolean
  submitLabel?: string
}

export function EnquiryForm({ onSubmit, submitting, serverFieldErrors, source = 'admin-dashboard', customerFacing = false, submitLabel = 'Submit enquiry' }: Props) {
  const { register, handleSubmit, control, formState: { errors } } = useForm<EnquiryFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { customer_name: '', phone: '', email: '', message: '' },
  })
  const messageLength = useWatch({ control, name: 'message' })?.length ?? 0
  const err = (k: keyof EnquiryFormValues) => errors[k]?.message ?? serverFieldErrors?.[k]

  return (
    <form
      noValidate
      onSubmit={handleSubmit((v) => onSubmit({ customer_name: v.customer_name, phone: v.phone, email: v.email, message: v.message, source }))}
      className="space-y-5"
    >
      <div className="grid gap-5 sm:grid-cols-2">
        <Field label={customerFacing ? 'Your name' : 'Customer name'} htmlFor="customer_name" error={err('customer_name')}>
          <input id="customer_name" autoComplete={customerFacing ? 'name' : 'off'} placeholder="Rahul Sharma" aria-invalid={!!err('customer_name')} className={inputCls(!!err('customer_name'))} {...register('customer_name')} />
        </Field>
        <Field label="Phone number" htmlFor="phone" error={err('phone')}>
          <input id="phone" type="tel" autoComplete={customerFacing ? 'tel' : 'off'} placeholder="+91 98765 43210" aria-invalid={!!err('phone')} className={inputCls(!!err('phone'))} {...register('phone')} />
        </Field>
      </div>
      <Field label="Email address" htmlFor="email" error={err('email')}>
        <input id="email" type="email" autoComplete={customerFacing ? 'email' : 'off'} placeholder="rahul@example.com" aria-invalid={!!err('email')} className={inputCls(!!err('email'))} {...register('email')} />
      </Field>
      <Field label={customerFacing ? 'How can we help?' : 'Enquiry message'} htmlFor="message" error={err('message')}>
        <textarea
          id="message" rows={6} aria-invalid={!!err('message')} className={inputCls(!!err('message')) + ' resize-y'}
          placeholder={customerFacing ? 'Tell us about your project: what you need, roughly when, and any budget you have in mind. English or Hindi is fine.' : 'Describe what the customer needs, in any language.'}
          {...register('message')}
        />
        <p className="mt-1 text-right text-xs text-slate-400">{messageLength}/5000</p>
      </Field>
      <div className="flex justify-end">
        <Button type="submit" loading={submitting} icon={<Send className="size-4" />}>{submitLabel}</Button>
      </div>
    </form>
  )
}
