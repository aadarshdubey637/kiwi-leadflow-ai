/** Warm paper background with a few very soft, desaturated colour washes — enough for the glass panels to have something to blur, without looking like a neon gradient. */
export function Backdrop() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-[#f4efe7]">
      <div className="absolute -left-40 -top-40 size-[38rem] animate-drift rounded-full bg-[#9bbf9f]/35 blur-3xl" />
      <div className="absolute -right-32 top-0 size-[32rem] rounded-full bg-[#e7c58f]/35 blur-3xl" />
      <div className="absolute -bottom-48 left-1/3 size-[40rem] animate-drift rounded-full bg-[#9db9cf]/30 blur-3xl [animation-delay:-20s]" />
      <div className="absolute bottom-10 right-10 size-[18rem] rounded-full bg-[#d98b6f]/15 blur-3xl" />
    </div>
  )
}
