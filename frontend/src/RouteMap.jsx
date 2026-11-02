import { useEffect } from 'react'
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './RouteMap.css'

function FitRoute({ points }) {
  const map = useMap()

  useEffect(() => {
    if (points.length === 1) map.setView(points[0], 13)
    if (points.length > 1) map.fitBounds(points, { padding: [28, 28], maxZoom: 13 })
  }, [map, points])

  return null
}

export default function RouteMap({ route, destination }) {
  const points = (route?.geometry || []).filter((point) => Array.isArray(point) && point.length >= 2)
  if (!points.length) return null

  const start = points[0]
  const end = points.at(-1)

  return (
    <section className="route-map-panel" aria-labelledby="route-map-title">
      <div className="route-map-heading">
        <div>
          <span className="eyebrow dark">Tuyến đường trực quan</span>
          <h3 id="route-map-title">Đến {destination?.name}</h3>
        </div>
        <p><strong>{route.distance_label}</strong> · {route.duration_label}</p>
      </div>
      <MapContainer className="route-map" center={start} zoom={11} scrollWheelZoom={false} aria-label={`Bản đồ tuyến đường đến ${destination?.name}`}>
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <FitRoute points={points} />
        <Polyline positions={points} pathOptions={{ color: '#E8A33D', weight: 4, opacity: 0.95 }} />
        <CircleMarker center={start} radius={9} pathOptions={{ color: '#0F3D3E', fillColor: '#0F3D3E', fillOpacity: 1, weight: 3 }}>
          <Tooltip direction="top">Điểm xuất phát</Tooltip>
        </CircleMarker>
        <CircleMarker center={end} radius={9} pathOptions={{ color: '#FAF6EF', fillColor: '#E8A33D', fillOpacity: 1, weight: 3 }}>
          <Tooltip direction="top">Điểm đến</Tooltip>
        </CircleMarker>
      </MapContainer>
      {route.provider === 'haversine-fallback' && <p className="route-map-note">Đường đi ước tính (chim bay)</p>}
      <a className="travel-button travel-button--outline route-google-link" href={route.google_maps_url} target="_blank" rel="noreferrer">Mở Google Maps để chỉ đường</a>
    </section>
  )
}
