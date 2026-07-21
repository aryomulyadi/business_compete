type IconProps = { className?: string; size?: number }

/* eslint-disable react/display-name */

function createIcon(path: string, viewBox = '0 0 24 24') {
  return ({ className, size = 20 }: IconProps) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={viewBox}
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {path}
    </svg>
  )
}

const p = (d: string) => <path d={d} />

export const IconHome = createIcon(
  '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'
)

export const IconHistory = createIcon(
  '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>'
)

export const IconSearch = createIcon(
  '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'
)

export const IconPalette = createIcon(
  '<circle cx="13.5" cy="6.5" r="0.5" fill="currentColor"/><circle cx="17.5" cy="10.5" r="0.5" fill="currentColor"/><circle cx="8.5" cy="7.5" r="0.5" fill="currentColor"/><circle cx="6.5" cy="12.5" r="0.5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-1 0-.83.67-1.5 1.5-1.5H16c3.31 0 6-2.69 6-6 0-5.52-4.5-10-10-10z"/>'
)

export const IconDownload = createIcon(
  '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>'
)

export const IconChevronRight = createIcon(
  '<polyline points="9 18 15 12 9 6"/>'
)

export const IconClose = createIcon(
  '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>'
)

export const IconCheck = createIcon(
  '<polyline points="20 6 9 17 4 12"/>'
)

export const IconAlert = createIcon(
  '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'
)

export const IconSparkle = createIcon(
  '<path d="M12 3l1.9 5.8a1 1 0 0 0 .95.69L20.8 10l-4.5 3.3a1 1 0 0 0-.36 1.12l1.7 5.2-4.4-3.2a1 1 0 0 0-1.18 0l-4.4 3.2 1.7-5.2a1 1 0 0 0-.36-1.12L3.2 10l5.95-.51a1 1 0 0 0 .95-.69z"/>'
)
