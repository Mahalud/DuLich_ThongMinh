import { createContext, useContext } from 'react'

export const OriginContext = createContext(null)

export function useOrigin() {
  const context = useContext(OriginContext)
  if (!context) throw new Error('useOrigin must be used inside the application origin provider')
  return context
}
