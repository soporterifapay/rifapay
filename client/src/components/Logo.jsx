/** Logo RifaPay en SVG inline (nítido a cualquier tamaño, sin assets).
 *  variant="drum"   -> bombo minimalista + ticket (recomendada)
 *  variant="ticket" -> ticket inclinado con check ámbar
 */
export function LogoMark({ variant = 'drum', size = 36 }) {
  if (variant === 'ticket') {
    return (
      <svg width={size} height={size} viewBox="0 0 48 48" role="img" aria-label="RifaPay">
        <g transform="rotate(-12 24 24)">
          <rect x="7" y="14" width="34" height="20" rx="5" fill="#059669" />
          <line x1="17" y1="15.5" x2="17" y2="32.5" stroke="#ffffff" strokeOpacity="0.55" strokeWidth="1.6" strokeDasharray="2.4 2" />
          <path d="M22 24.5l4.5 4.5L34 20" stroke="#FBBF24" strokeWidth="4.2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </g>
      </svg>
    )
  }
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" role="img" aria-label="RifaPay">
      <path d="M15 40l5.5-13M33 40l-5.5-13" stroke="#047857" strokeWidth="3.2" strokeLinecap="round" />
      <path d="M10 42.5h28" stroke="#047857" strokeWidth="3.2" strokeLinecap="round" />
      <rect x="12" y="11" width="24" height="17" rx="8.5" fill="#059669" />
      <rect x="12" y="16" width="24" height="4" fill="#047857" opacity="0.55" />
      <circle cx="24" cy="19.5" r="2.2" fill="#ffffff" opacity="0.85" />
      <path d="M36.5 19.5H42v4.5" stroke="#065f46" strokeWidth="2.4" fill="none" strokeLinecap="round" />
      <circle cx="42" cy="26.5" r="2.2" fill="#065f46" />
      <g transform="rotate(18 38 7)">
        <rect x="33" y="3.5" width="10" height="7" rx="1.6" fill="#ffffff" stroke="#047857" strokeWidth="1.6" />
        <line x1="36.2" y1="3.8" x2="36.2" y2="10.2" stroke="#047857" strokeWidth="1" strokeDasharray="1.4 1.2" />
      </g>
    </svg>
  )
}

export function Logo({ variant = 'drum' }) {
  return (
    <span className="inline-flex items-center gap-2">
      <LogoMark variant={variant} size={36} />
      <span className="text-2xl font-extrabold tracking-tight text-brand-800">RifaPay</span>
    </span>
  )
}
