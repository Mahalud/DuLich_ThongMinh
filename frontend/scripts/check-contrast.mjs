import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const css = readFileSync(resolve('src/App.css'), 'utf8')
const variables = new Map()
for (const block of css.matchAll(/:root\s*\{([^}]*)\}/g)) {
  for (const [, name, value] of block[1].matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
    variables.set(name, value.trim())
  }
}

function resolveColor(input, seen = new Set()) {
  const ref = input.match(/^var\((--[\w-]+)(?:,\s*([^)]*))?\)$/)
  if (ref) {
    if (seen.has(ref[1])) throw new Error(`Vòng tham chiếu biến màu: ${ref[1]}`)
    const value = variables.get(ref[1]) || ref[2]
    if (!value) throw new Error(`Không tìm thấy biến màu ${ref[1]}`)
    seen.add(ref[1])
    return resolveColor(value, seen)
  }
  const hex = input.match(/^#([\da-f]{3}|[\da-f]{6})$/i)?.[1]
  if (!hex) throw new Error(`Chỉ hỗ trợ màu hex hoặc biến CSS trong phép kiểm tra: ${input}`)
  const full = hex.length === 3 ? [...hex].map((part) => part + part).join('') : hex
  return [0, 2, 4].map((offset) => Number.parseInt(full.slice(offset, offset + 2), 16) / 255)
}

function luminance(color) {
  return color.map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4)
    .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0)
}

function contrast(foreground, background) {
  const asColor = (value) => value.startsWith('--') ? `var(${value})` : value
  const [lighter, darker] = [luminance(resolveColor(asColor(foreground))), luminance(resolveColor(asColor(background)))].sort((a, b) => b - a)
  return (lighter + 0.05) / (darker + 0.05)
}

const pairs = [
  { label: 'Chữ chính trên nền kem', fg: '--text', bg: '--bg', minimum: 4.5 },
  { label: 'Chữ chính trên nền trắng', fg: '--text', bg: '--color-white', minimum: 4.5 },
  { label: 'Chữ phụ trên nền kem', fg: '--text-muted', bg: '--bg', minimum: 4.5 },
  { label: 'Chữ phụ trên nền trắng', fg: '--text-muted', bg: '--color-white', minimum: 4.5 },
  { label: 'Chữ nhập liệu trên nền trắng', fg: '--text', bg: '--color-white', minimum: 4.5 },
  { label: 'Placeholder trên nền trắng', fg: '--text-muted', bg: '--color-white', minimum: 3 },
  { label: 'Chữ chính trên màu cam thương hiệu', fg: '--text', bg: '--color-orange', minimum: 4.5 },
  { label: 'Chữ nút CTA trên cam đậm', fg: '#FFFFFF', bg: '#A9470A', minimum: 4.5 },
  { label: 'Chữ nút hủy đơn trên nền trắng', fg: '#7F1D1D', bg: '#FFFFFF', minimum: 4.5 },
  { label: 'Chữ nút hủy đơn khi vô hiệu', fg: '#6B4B4B', bg: '#F3EEEE', minimum: 3 },
  { label: 'Chữ trên hero tối', fg: '--on-dark', bg: '--color-navy', minimum: 4.5 },
  { label: 'Nút vô hiệu', fg: '--disabled-text', bg: '--disabled-bg', minimum: 3 },
]

let failed = false
for (const pair of pairs) {
  const ratio = contrast(pair.fg, pair.bg)
  const result = ratio >= pair.minimum ? 'ĐẠT' : 'LỖI'
  console.log(`${result} ${pair.label}: ${ratio.toFixed(2)}:1 (yêu cầu ${pair.minimum}:1)`)
  if (ratio < pair.minimum) failed = true
}

if (failed) process.exitCode = 1
