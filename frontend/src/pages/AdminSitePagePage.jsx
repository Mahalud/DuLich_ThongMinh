import { useEffect, useState } from 'react'
import { ArrowDown, ArrowUp, Plus, Save, Trash2 } from 'lucide-react'
import { api } from '../api'
import { AdminLayout } from './AdminPages'
import SitePageView from '../components/SitePageView'
import { ErrorNotice } from '../components/DesignSystem'

const blankSection = { title: '', content: '', image_url: '', layout: 'text' }

export default function AdminSitePagePage() {
  const [page, setPage] = useState(null)
  const [pageForm, setPageForm] = useState({ title: '', cover_image_url: '', intro: '' })
  const [sectionForm, setSectionForm] = useState(blankSection)
  const [editingId, setEditingId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const load = () => api('/api/pages/gioi-thieu/').then((data) => {
    setPage(data)
    setPageForm({ title: data.title || '', cover_image_url: data.cover_image_url || '', intro: data.intro || '' })
  }).catch((err) => setError(err.message || 'Không tải được trang giới thiệu.')).finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const savePage = async (event) => {
    event.preventDefault()
    setSaving(true); setError(''); setNotice('')
    try {
      const updated = await api('/api/admin/pages/gioi-thieu/', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(pageForm),
      })
      setPage(updated)
      setPageForm({ title: updated.title, cover_image_url: updated.cover_image_url || '', intro: updated.intro || '' })
      setNotice('Thông tin trang đã được lưu.')
    } catch (err) { setError(err.message || 'Không lưu được thông tin trang.') }
    finally { setSaving(false) }
  }

  const saveSection = async (event) => {
    event.preventDefault()
    setSaving(true); setError(''); setNotice('')
    const path = editingId
      ? `/api/admin/pages/gioi-thieu/sections/${editingId}/`
      : '/api/admin/pages/gioi-thieu/sections/'
    try {
      const saved = await api(path, {
        method: editingId ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sectionForm),
      })
      const sections = [...(page.sections || [])]
      if (editingId) {
        const index = sections.findIndex((section) => section.id === editingId)
        if (index >= 0) sections[index] = saved
      } else sections.push(saved)
      setPage({ ...page, sections: sections.sort((a, b) => a.order - b.order || a.id - b.id) })
      setSectionForm(blankSection); setEditingId(null)
      setNotice(editingId ? 'Phần nội dung đã được cập nhật.' : 'Đã thêm phần nội dung.')
    } catch (err) { setError(err.message || 'Không lưu được phần nội dung.') }
    finally { setSaving(false) }
  }

  const editSection = (section) => {
    setEditingId(section.id)
    setSectionForm({ title: section.title || '', content: section.content || '', image_url: section.image_url || '', layout: section.layout || 'text' })
    setNotice('')
  }

  const deleteSection = async (section) => {
    if (!window.confirm(`Xóa phần “${section.title}”?`)) return
    setError(''); setNotice('')
    try {
      await api(`/api/admin/pages/gioi-thieu/sections/${section.id}/`, { method: 'DELETE' })
      setPage({ ...page, sections: page.sections.filter((item) => item.id !== section.id) })
      if (editingId === section.id) { setEditingId(null); setSectionForm(blankSection) }
      setNotice('Đã xóa phần nội dung.')
    } catch (err) { setError(err.message || 'Không xóa được phần nội dung.') }
  }

  const moveSection = async (index, direction) => {
    const sections = [...(page?.sections || [])]
    const target = index + direction
    if (target < 0 || target >= sections.length) return
    ;[sections[index], sections[target]] = [sections[target], sections[index]]
    const ordered = sections.map((section, order) => ({ ...section, order }))
    setPage({ ...page, sections: ordered })
    try {
      const updated = await api('/api/admin/pages/gioi-thieu/sections/reorder/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ section_ids: ordered.map((section) => section.id) }),
      })
      setPage(updated)
    } catch (err) { setError(err.message || 'Không đổi được thứ tự phần nội dung.'); load() }
  }

  const previewSections = (page?.sections || []).map((section) => editingId === section.id ? { ...section, ...sectionForm } : section)
  const hasSectionDraft = !editingId && (sectionForm.title.trim() || sectionForm.content.trim())
  if (hasSectionDraft) previewSections.push({ ...sectionForm, id: 'draft', order: previewSections.length })

  if (loading) return <AdminLayout title="Trang giới thiệu"><div className="admin-list">Đang tải nội dung…</div></AdminLayout>

  return <AdminLayout title="Trang giới thiệu">
    {error && <ErrorNotice>{error}</ErrorNotice>}
    {notice && <p className="admin-message" role="status">{notice}</p>}
    <div className="site-admin-grid">
      <div className="site-admin-editor">
        <form className="admin-form site-admin-page-form" onSubmit={savePage}>
          <h2>Thông tin trang</h2>
          <label>Tiêu đề<input required maxLength={200} value={pageForm.title} onChange={(event) => setPageForm({ ...pageForm, title: event.target.value })} /></label>
          <label>Ảnh bìa (URL)<input type="url" value={pageForm.cover_image_url} onChange={(event) => setPageForm({ ...pageForm, cover_image_url: event.target.value })} placeholder="https://…" /></label>
          <label>Đoạn mở đầu<textarea rows={4} value={pageForm.intro} onChange={(event) => setPageForm({ ...pageForm, intro: event.target.value })} /></label>
          <button className="primary-btn" type="submit" disabled={saving}><Save size={16} /> {saving ? 'Đang lưu…' : 'Lưu thông tin trang'}</button>
        </form>

        <section className="admin-list site-admin-sections">
          <div className="site-admin-section-heading"><h2>Các phần nội dung</h2><span>{page?.sections?.length || 0} phần</span></div>
          {(page?.sections || []).map((section, index) => <article className="site-admin-section-row" key={section.id}>
            <div><strong>{section.title}</strong><small>{section.layout} · {section.content.slice(0, 95)}{section.content.length > 95 ? '…' : ''}</small></div>
            <div className="site-admin-row-actions">
              <button className="travel-button travel-button--outline" type="button" aria-label="Di chuyển lên" disabled={index === 0} onClick={() => moveSection(index, -1)}><ArrowUp size={16} /></button>
              <button className="travel-button travel-button--outline" type="button" aria-label="Di chuyển xuống" disabled={index === page.sections.length - 1} onClick={() => moveSection(index, 1)}><ArrowDown size={16} /></button>
              <button className="travel-button travel-button--outline" type="button" onClick={() => editSection(section)}>Sửa</button>
              <button className="travel-button travel-button--outline site-admin-delete" type="button" onClick={() => deleteSection(section)}><Trash2 size={15} /> Xóa</button>
            </div>
          </article>)}
          {!page?.sections?.length && <p className="detail-muted">Trang chưa có phần nội dung nào.</p>}
        </section>

        <form className="admin-form site-admin-section-form" onSubmit={saveSection}>
          <h2>{editingId ? 'Sửa phần nội dung' : 'Thêm phần nội dung'}</h2>
          <label>Tiêu đề<input required maxLength={200} value={sectionForm.title} onChange={(event) => setSectionForm({ ...sectionForm, title: event.target.value })} /></label>
          <label>Nội dung<textarea rows={7} value={sectionForm.content} onChange={(event) => setSectionForm({ ...sectionForm, content: event.target.value })} placeholder={'Đoạn văn bản\n- Mục danh sách\n**Chữ in đậm**'} /></label>
          <label>Ảnh minh họa (URL)<input type="url" value={sectionForm.image_url} onChange={(event) => setSectionForm({ ...sectionForm, image_url: event.target.value })} placeholder="https://…" /></label>
          <label>Bố cục<select value={sectionForm.layout} onChange={(event) => setSectionForm({ ...sectionForm, layout: event.target.value })}><option value="text">Văn bản</option><option value="image_left">Ảnh trái</option><option value="image_right">Ảnh phải</option><option value="cards">Thẻ</option></select></label>
          <div className="site-admin-form-actions"><button className="primary-btn" type="submit" disabled={saving}>{editingId ? 'Lưu phần' : <><Plus size={16} /> Thêm phần</>}</button>{editingId && <button className="travel-button travel-button--outline" type="button" onClick={() => { setEditingId(null); setSectionForm(blankSection) }}>Hủy sửa</button>}</div>
        </form>
      </div>
      <aside className="site-admin-preview"><h2>Xem trước trang công khai</h2><div className="site-admin-preview-frame"><SitePageView page={{ ...page, ...pageForm, sections: previewSections }} showStats={false} /></div></aside>
    </div>
  </AdminLayout>
}
