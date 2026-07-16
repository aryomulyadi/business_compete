import { IconChevronRight } from './Icons'

interface BreadcrumbLink {
  label: string
  href?: string
}

export default function Breadcrumbs({ links }: { links: BreadcrumbLink[] }) {
  if (links.length === 0) return null

  return (
    <nav className="flex items-center gap-1 text-sm mb-5">
      {links.map((link, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && <IconChevronRight size={12} className="text-[#475569]" />}
          {link.href ? (
            <a
              href={link.href}
              className="text-[#64748B] hover:text-[#94A3B8] transition-colors"
            >
              {link.label}
            </a>
          ) : (
            <span className="text-[#CBD5E1] font-medium">{link.label}</span>
          )}
        </span>
      ))}
    </nav>
  )
}
