import { Check, Users } from 'lucide-react'
import { amenityIcon } from '../amenityIcons'

export default function RoomTypeCard({ room, labels = {}, onBook }) {
  return <article className="room-item room-type-card">
    <div className="room-type-main"><div className="room-type-copy"><span className="room-availability"><Check size={14} /> Còn {room.stock} phòng</span><h3>{room.name}</h3><span className="room-capacity"><Users size={15} /> Phù hợp cho khách du lịch</span></div><strong className="room-type-price">{Number(room.base_price).toLocaleString('vi-VN')} <small>đ / đêm</small></strong></div>
    <div className="room-type-bottom"><div className="amenity-list" aria-label="Tiện ích phòng">{(room.amenities || []).map((key) => <span className="amenity-icon" title={labels[key] || key} aria-label={labels[key] || key} key={key}>{amenityIcon(key, 17)}</span>)}</div><button type="button" className="travel-button travel-button--primary" onClick={() => onBook(room)}>Chọn phòng</button></div>
  </article>
}
