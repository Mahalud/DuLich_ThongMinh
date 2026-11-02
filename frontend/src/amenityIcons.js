import { AirVent, ArrowUpDown, Bath, ChefHat, CircleHelp, Coffee, DoorOpen, Droplets, ParkingCircle, Tv, WashingMachine, Waves, Wifi } from 'lucide-react'
import { createElement } from 'react'

export const amenityIconMap = {
  wifi: Wifi,
  dieu_hoa: AirVent,
  bon_tam: Bath,
  huong_bien: Waves,
  ho_boi: Droplets,
  bua_sang: Coffee,
  do_xe: ParkingCircle,
  thang_may: ArrowUpDown,
  bep: ChefHat,
  giat_ui: WashingMachine,
  tivi: Tv,
  ban_cong: DoorOpen,
}

export const amenityIcon = (key, size = 15) => {
  const Icon = amenityIconMap[amenityCatalog[key]?.icon_name || key] || CircleHelp
  return createElement(Icon, { size, 'aria-hidden': true })
}

export const amenityIconOptions = Object.keys(amenityIconMap)

let amenityCatalog = {}

export const setAmenityCatalog = (items) => {
  const list = Array.isArray(items) ? items : Array.isArray(items?.results) ? items.results : []
  amenityCatalog = Object.fromEntries(list.filter((item) => item && typeof item.key === 'string').map((item) => [item.key, item]))
}

export const amenityLabel = (key) => amenityCatalog[key]?.label || key

export const amenityIconName = (key) => amenityCatalog[key]?.icon_name || key
