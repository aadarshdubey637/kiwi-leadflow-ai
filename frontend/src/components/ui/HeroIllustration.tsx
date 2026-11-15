/** Hand-built flat illustration (no external image): an enquiry form, the reply coming back, and a sticky note. */
export function HeroIllustration({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 420 340" className={className} role="img" aria-label="Illustration of an enquiry form and a reply">
      {/* soft colour shapes behind */}
      <circle cx="120" cy="120" r="110" fill="#9bbf9f" opacity="0.38" />
      <circle cx="330" cy="240" r="90" fill="#e7c58f" opacity="0.5" />
      <path d="M30 300c40-30 90-20 130-40" stroke="#c4553a" strokeWidth="3" strokeLinecap="round" fill="none" opacity="0.35" />

      {/* browser window with the form */}
      <g>
        <rect x="46" y="44" width="270" height="206" rx="18" fill="#fffdf9" stroke="#e0d8ca" />
        <path d="M46 78h270" stroke="#ece5d8" />
        <circle cx="68" cy="61" r="5" fill="#c4553a" />
        <circle cx="86" cy="61" r="5" fill="#d9962b" />
        <circle cx="104" cy="61" r="5" fill="#7a9e7e" />
        <rect x="68" y="98" width="62" height="7" rx="3.5" fill="#d3cbbd" />
        <rect x="68" y="110" width="104" height="24" rx="7" fill="#f3efe9" stroke="#e6e0d6" />
        <rect x="184" y="98" width="62" height="7" rx="3.5" fill="#d3cbbd" />
        <rect x="184" y="110" width="110" height="24" rx="7" fill="#f3efe9" stroke="#e6e0d6" />
        <rect x="68" y="146" width="80" height="7" rx="3.5" fill="#d3cbbd" />
        <rect x="68" y="158" width="226" height="48" rx="7" fill="#f3efe9" stroke="#e6e0d6" />
        <rect x="78" y="168" width="150" height="5" rx="2.5" fill="#cfc6b6" />
        <rect x="78" y="179" width="110" height="5" rx="2.5" fill="#cfc6b6" />
        <rect x="222" y="214" width="72" height="22" rx="8" fill="#175a55" />
        <rect x="236" y="223" width="44" height="4" rx="2" fill="#f4efe7" />
      </g>

      {/* the reply */}
      <g>
        <path d="M232 168h128a16 16 0 0 1 16 16v54a16 16 0 0 1-16 16h-92l-26 20 4-20h-14a16 16 0 0 1-16-16v-54a16 16 0 0 1 16-16z" fill="#175a55" />
        <rect x="248" y="188" width="96" height="6" rx="3" fill="#f4efe7" />
        <rect x="248" y="202" width="112" height="6" rx="3" fill="#f4efe7" opacity="0.75" />
        <rect x="248" y="216" width="70" height="6" rx="3" fill="#f4efe7" opacity="0.55" />
        <circle cx="352" cy="176" r="12" fill="#e0724f" />
        <path d="M346 176l4 4 7-8" stroke="#fffdf9" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      </g>

      {/* sticky note */}
      <g transform="rotate(-7 78 270)">
        <rect x="30" y="236" width="96" height="74" rx="6" fill="#f6dd9a" />
        <rect x="42" y="252" width="62" height="5" rx="2.5" fill="#b8892a" opacity="0.7" />
        <rect x="42" y="264" width="72" height="5" rx="2.5" fill="#b8892a" opacity="0.5" />
        <rect x="42" y="276" width="44" height="5" rx="2.5" fill="#b8892a" opacity="0.5" />
      </g>
    </svg>
  )
}
