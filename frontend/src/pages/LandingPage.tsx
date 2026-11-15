import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight, Bot, CheckCircle2, Code2, Globe, Lock, Mail, MapPin, Megaphone, MessageCircle, Phone, ShoppingBag, Smartphone,
} from 'lucide-react'
import { ApiError } from '@/api/axiosInstance'
import { EnquiryForm } from '@/components/enquiry/EnquiryForm'
import { Backdrop } from '@/components/ui/Backdrop'
import { Button, primaryLinkClass, secondaryLinkClass } from '@/components/ui/Button'
import { HeroIllustration } from '@/components/ui/HeroIllustration'
import { LogoMark } from '@/components/ui/Logo'
import { usePublicCreateEnquiry } from '@/hooks/useApi'
import type { EnquiryCreate } from '@/types/api'

const YEAR = new Date().getFullYear()

const SERVICES = [
  { icon: Globe, name: 'Website Development', text: 'Fast, modern business websites built with Next.js and React, easy to keep up to date.', tint: 'bg-[#d9ece8] text-[#175a55]' },
  { icon: Smartphone, name: 'Mobile App Development', text: 'Android and iOS apps in React Native and Flutter, from first screen to store release.', tint: 'bg-[#dbe7f0] text-[#2f6285]' },
  { icon: Bot, name: 'AI Software & Applications', text: 'Chatbots, document search and automation built around your own data.', tint: 'bg-[#eadde3] text-[#7a4558]' },
  { icon: Megaphone, name: 'Digital Marketing', text: 'SEO, social media and campaigns that reach the right customers.', tint: 'bg-[#f6e6c4] text-[#8f6410]' },
  { icon: ShoppingBag, name: 'E-commerce Development', text: 'Online stores with catalogues, payments and order tracking.', tint: 'bg-[#f6dcd3] text-[#a9452d]' },
  { icon: Code2, name: 'Custom Software & SaaS', text: 'CRM, ERP and attendance systems, dashboards and SaaS products shaped around how you work.', tint: 'bg-[#dbead9] text-[#2f6b3f]' },
  { icon: MessageCircle, name: 'Something else?', text: "Not on this list? Tell us anyway. We'll say honestly whether we can help.", tint: 'bg-[#ebe6dc] text-[#5b564b]' },
]

const STEPS = [
  { n: '1', title: 'Tell us what you need', text: 'Send a short note through the form. What you want built, roughly when, and any budget in mind.' },
  { n: '2', title: 'We read it carefully', text: 'Your enquiry is sorted by service and urgency so it reaches the right person quickly.' },
  { n: '3', title: 'You hear back from a person', text: 'We reply with questions, ideas and next steps, usually a short call to get the details right.' },
]

function ContactForm() {
  const create = usePublicCreateEnquiry()
  const [sent, setSent] = useState<{ id: number; name: string } | null>(null)
  const [formKey, setFormKey] = useState(0)

  const submit = async (values: EnquiryCreate) => {
    try {
      const e = await create.mutateAsync(values)
      setSent({ id: e.id, name: values.customer_name.split(' ')[0] })
    } catch {
      /* the hook already showed a friendly toast */
    }
  }

  if (sent) {
    return (
      <div role="status" className="flex flex-col items-center px-6 py-14 text-center">
        <div className="flex size-14 items-center justify-center rounded-full bg-[#dbead9] text-[#2f6b3f]">
          <CheckCircle2 className="size-7" aria-hidden />
        </div>
        <h3 className="mt-5 font-serif text-2xl text-slate-900">Thank you, {sent.name}.</h3>
        <p className="mt-2 max-w-sm text-sm text-slate-600">
          We've received your enquiry (reference <span className="font-semibold text-slate-800">#{sent.id}</span>). Someone from our team will get in touch soon.
        </p>
        <Button variant="secondary" className="mt-6" onClick={() => { setSent(null); setFormKey((k) => k + 1); create.reset() }}>
          Send another enquiry
        </Button>
      </div>
    )
  }

  return (
    <div className="p-6 sm:p-8">
      <EnquiryForm
        key={formKey}
        customerFacing
        source="website"
        submitLabel="Send enquiry"
        onSubmit={submit}
        submitting={create.isPending}
        serverFieldErrors={create.error instanceof ApiError ? create.error.fieldErrors : undefined}
      />
    </div>
  )
}

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <Backdrop />

      <header className="sticky top-4 z-30 mx-auto max-w-6xl px-4">
        <nav className="glass flex h-16 items-center justify-between rounded-2xl px-4 sm:px-5" aria-label="Site">
          <a href="#top" className="flex items-center gap-3">
            <LogoMark className="size-9" />
            <span className="leading-tight">
              <span className="block text-[15px] font-semibold tracking-tight text-slate-900">Kiwi Connect Digital</span>
              <span className="block text-[11px] text-slate-500">Custom software · Apps · AI</span>
            </span>
          </a>
          <div className="flex items-center gap-1 sm:gap-2">
            <a href="#services" className="hidden rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-white/60 sm:block">Services</a>
            <a href="#how" className="hidden rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-white/60 sm:block">How it works</a>
            <a href="#contact" className="hidden rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-white/60 sm:block">Contact</a>
            <Link to="/admin/login" className={secondaryLinkClass}><Lock className="size-4" aria-hidden /> Staff login</Link>
          </div>
        </nav>
      </header>

      <main id="top">
        {/* Hero */}
        <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 pb-16 pt-14 lg:grid-cols-2 lg:pt-20">
          <div>
            <p className="inline-block rounded-full bg-white/70 px-3 py-1 text-xs font-medium text-brand-700 ring-1 ring-inset ring-brand-200">
              A software company in India for startups and growing businesses
            </p>
            <h1 className="mt-5 font-serif text-4xl leading-[1.1] tracking-tight text-slate-900 sm:text-5xl lg:text-[3.4rem]">
              Have a project in mind? <span className="text-brand-600">Let's talk it through.</span>
            </h1>
            <p className="mt-5 max-w-lg text-lg leading-relaxed text-slate-600">
              Tell us what you need. Our team reads every enquiry and comes back with clear next steps, not a canned reply.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a href="#contact" className={`${primaryLinkClass} px-5 py-2.5 text-[15px]`}>Send an enquiry <ArrowRight className="size-4" aria-hidden /></a>
              <a href="#services" className={`${secondaryLinkClass} px-5 py-2.5 text-[15px]`}>What we do</a>
            </div>
            <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-600">
              {['Write in English or Hindi', 'No obligation', 'Your details stay private'].map((t) => (
                <li key={t} className="flex items-center gap-2"><CheckCircle2 className="size-4 text-brand-600" aria-hidden />{t}</li>
              ))}
            </ul>
          </div>
          <HeroIllustration className="mx-auto w-full max-w-lg drop-shadow-[0_20px_30px_rgba(60,45,30,0.12)]" />
        </section>

        {/* Services */}
        <section id="services" className="mx-auto max-w-6xl scroll-mt-28 px-4 py-16">
          <h2 className="font-serif text-3xl tracking-tight text-slate-900">What we can build for you</h2>
          <p className="mt-2 max-w-xl text-slate-600">Seven areas we work in, from websites and mobile apps to AI tools and marketing. Not sure which one fits? Just describe the problem.</p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {SERVICES.map(({ icon: Icon, name, text, tint }, i) => (
              <article key={name} className={`glass rounded-2xl p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg ${i === SERVICES.length - 1 ? 'sm:col-span-2 lg:col-span-3 lg:flex lg:items-center lg:gap-5' : ''}`}>
                <div className={`flex size-11 items-center justify-center rounded-xl ${tint}`}><Icon className="size-5" aria-hidden /></div>
                <h3 className="mt-4 font-semibold text-slate-900">{name}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{text}</p>
              </article>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section id="how" className="mx-auto max-w-6xl scroll-mt-28 px-4 py-16">
          <h2 className="font-serif text-3xl tracking-tight text-slate-900">How it works</h2>
          <ol className="mt-8 grid gap-4 md:grid-cols-3">
            {STEPS.map((s) => (
              <li key={s.n} className="glass rounded-2xl p-6">
                <span className="font-serif text-4xl text-clay">{s.n}</span>
                <h3 className="mt-3 font-semibold text-slate-900">{s.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{s.text}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* Contact */}
        <section id="contact" className="mx-auto max-w-6xl scroll-mt-28 px-4 py-16">
          <div className="grid gap-8 lg:grid-cols-5">
            <div className="lg:col-span-2">
              <h2 className="font-serif text-3xl tracking-tight text-slate-900">Send us an enquiry</h2>
              <p className="mt-3 text-slate-600">
                The more you tell us, the better our first reply. Mention what you want built, when you'd like it ready, and a budget if you have one. If you don't, that's fine too.
              </p>
              <ul className="mt-6 space-y-3 text-sm text-slate-700">
                <li className="flex items-start gap-3"><Phone className="mt-0.5 size-4 shrink-0 text-brand-600" aria-hidden /><a href="tel:+918305959538" className="hover:underline">+91 83059 59538</a></li>
                <li className="flex items-start gap-3"><Mail className="mt-0.5 size-4 shrink-0 text-brand-600" aria-hidden /><a href="mailto:kiwiconnectdigital@gmail.com" className="hover:underline">kiwiconnectdigital@gmail.com</a></li>
                <li className="flex items-start gap-3"><MapPin className="mt-0.5 size-4 shrink-0 text-brand-600" aria-hidden /><span>Second Floor, R-59, GRP Colony, Zone 2, Maharana Pratap Nagar, Bhopal, Madhya Pradesh 462011</span></li>
              </ul>
              <p className="mt-6 flex items-start gap-2 text-sm text-slate-500">
                <Lock className="mt-0.5 size-4 shrink-0" aria-hidden />
                We only use your details to reply to this enquiry.
              </p>
            </div>
            <div className="glass-strong rounded-3xl lg:col-span-3">
              <ContactForm />
            </div>
          </div>
        </section>
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 pt-6">
        <div className="flex flex-col items-center justify-between gap-3 border-t border-slate-300/60 pt-6 text-sm text-slate-500 sm:flex-row">
          <p>© {YEAR} Kiwi Connect Digital · Bhopal, India</p>
          <Link to="/admin/login" className="hover:text-slate-800">Staff login</Link>
        </div>
      </footer>
    </div>
  )
}
