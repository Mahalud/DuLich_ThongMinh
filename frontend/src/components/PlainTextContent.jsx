import { Fragment } from 'react'

function safeHttpUrl(value) {
  try {
    const url = new URL(value)
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : null
  } catch {
    return null
  }
}

function inlineParts(text) {
  const pattern = /(\*\*[^*]+\*\*|\[[^\]]+\]\(https?:\/\/[^)\s]+\)|https?:\/\/[^\s]+)/g
  const parts = []
  let cursor = 0
  for (const match of text.matchAll(pattern)) {
    const index = match.index ?? 0
    if (index > cursor) parts.push(text.slice(cursor, index))
    const token = match[0]
    if (token.startsWith('**')) {
      parts.push(<strong key={`bold-${index}`}>{token.slice(2, -2)}</strong>)
    } else {
      const markdown = token.match(/^\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)$/)
      const candidate = markdown?.[2] || token
      const url = safeHttpUrl(candidate)
      if (url) {
        const trailing = markdown ? '' : (candidate.match(/[.,!?;:)]+$/)?.[0] || '')
        const href = trailing ? candidate.slice(0, -trailing.length) : candidate
        const safeHref = safeHttpUrl(href)
        parts.push(safeHref ? <Fragment key={`link-${index}`}><a href={safeHref} target="_blank" rel="noopener noreferrer">{markdown?.[1] || href}</a>{trailing}</Fragment> : token)
      } else {
        parts.push(token)
      }
    }
    cursor = index + token.length
  }
  if (cursor < text.length) parts.push(text.slice(cursor))
  return parts.map((part, index) => typeof part === 'string' ? <Fragment key={`text-${index}`}>{part}</Fragment> : part)
}

export function PlainTextContent({ content = '', className = '' }) {
  const lines = String(content).replace(/\r\n?/g, '\n').split('\n')
  const blocks = []
  let paragraph = []
  let bullets = []
  const flushParagraph = () => {
    if (paragraph.length) blocks.push(<p key={`p-${blocks.length}`}>{inlineParts(paragraph.join(' '))}</p>)
    paragraph = []
  }
  const flushBullets = () => {
    if (bullets.length) blocks.push(<ul key={`ul-${blocks.length}`}>{bullets.map((line, index) => <li key={index}>{inlineParts(line)}</li>)}</ul>)
    bullets = []
  }

  lines.forEach((line) => {
    const trimmed = line.trim()
    const bullet = trimmed.match(/^[-*]\s+(.+)$/)
    if (bullet) {
      flushParagraph()
      bullets.push(bullet[1])
    } else if (!trimmed) {
      flushParagraph()
      flushBullets()
    } else {
      flushBullets()
      paragraph.push(trimmed)
    }
  })
  flushParagraph()
  flushBullets()
  return <div className={`plain-text-content ${className}`.trim()}>{blocks}</div>
}
