import assert from 'node:assert/strict'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'

const vite = await createServer({ server: { middlewareMode: true }, appType: 'custom' })
try {
  const { PlainTextContent } = await vite.ssrLoadModule('/src/components/PlainTextContent.jsx')
  const markup = renderToStaticMarkup(React.createElement(PlainTextContent, {
    content: '<script>alert("x")</script> **đậm**\n- mục\n[liên kết](https://example.com)',
  }))
  assert.match(markup, /&lt;script&gt;alert\(&quot;x&quot;\)&lt;\/script&gt;/)
  assert.doesNotMatch(markup, /<script>/)
  assert.match(markup, /<strong>đậm<\/strong>/)
  assert.match(markup, /<ul>/)
  assert.match(markup, /href="https:\/\/example\.com\/?"/)
  process.stdout.write('PlainTextContent: HTML hiển thị như văn bản an toàn.\n')
} finally {
  await vite.close()
}
