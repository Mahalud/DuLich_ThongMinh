export const TRIP_PLAN_STORAGE_KEY = 'di-viet-nam-trip-plan-v1'

function localDateString(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function isValidDateString(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return false
  const parsed = new Date(`${value}T12:00:00`)
  return Number.isFinite(parsed.getTime()) && localDateString(parsed) === value
}

export function createEmptyTripPlan() {
  return { startDate: localDateString(), durationDays: 3, stops: [] }
}

export function readTripPlan() {
  try {
    const saved = JSON.parse(localStorage.getItem(TRIP_PLAN_STORAGE_KEY) || 'null')
    if (!saved || !Array.isArray(saved.stops)) return createEmptyTripPlan()
    const durationDays = Math.max(1, Math.min(14, Number(saved.durationDays) || 3))
    const seen = new Set()
    const stops = saved.stops.reduce((items, stop) => {
      const id = Number(stop?.destinationId)
      if (!Number.isInteger(id) || seen.has(id)) return items
      seen.add(id)
      items.push({ destinationId: id, day: Math.max(1, Math.min(durationDays, Number(stop.day) || 1)) })
      return items
    }, [])
    return {
      startDate: isValidDateString(saved.startDate) ? saved.startDate : localDateString(),
      durationDays,
      stops,
    }
  } catch {
    return createEmptyTripPlan()
  }
}

export function saveTripPlan(plan) {
  try { localStorage.setItem(TRIP_PLAN_STORAGE_KEY, JSON.stringify(plan)) } catch {}
}
