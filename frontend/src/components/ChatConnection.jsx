import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api, backendUrl } from '../api'

const ChatConnectionContext = createContext(null)
const SOUND_KEY = 'travel-chat-sound-enabled'

export function ChatConnectionProvider({ user, authStatus, children }) {
  const [connection, setConnection] = useState('Đang kết nối')
  const [unreadCount, setUnreadCount] = useState(0)
  const [soundEnabled, setSoundEnabled] = useState(() => localStorage.getItem(SOUND_KEY) === 'true')
  const socketRef = useRef(null)
  const activeConversationsRef = useRef(new Set())
  const soundEnabledRef = useRef(soundEnabled)
  const unreadRef = useRef(0)
  const previousTitleRef = useRef('')
  const authKeyRef = useRef('')
  const authVersionRef = useRef(0)
  const nextAuthKey = authStatus === 'authenticated' && user?.id ? String(user.id) : ''
  if (authKeyRef.current !== nextAuthKey) {
    authKeyRef.current = nextAuthKey
    authVersionRef.current += 1
  }
  soundEnabledRef.current = soundEnabled

  const syncUnread = useCallback(async () => {
    const authVersion = authVersionRef.current
    if (!authKeyRef.current) return 0
    const data = await api('/api/chat/unread-count/')
    if (authVersionRef.current !== authVersion) return 0
    const count = Number(data?.count || 0)
    unreadRef.current = count
    setUnreadCount(count)
    return count
  }, [])

  const markRead = useCallback(async (conversationId) => {
    if (!conversationId) return
    const authVersion = authVersionRef.current
    if (!authKeyRef.current) return
    try {
      const data = await api(`/api/chat/conversations/${conversationId}/read/`, { method: 'POST' })
      if (authVersionRef.current !== authVersion) return
      const count = Number(data?.count ?? 0)
      unreadRef.current = count
      setUnreadCount(count)
    } catch {
      // The next socket reconnect re-syncs counts if marking read is temporarily unavailable.
    }
  }, [])

  const setConversationActive = useCallback((conversationId, active) => {
    const id = Number(conversationId)
    if (!id) return
    if (active) {
      activeConversationsRef.current.add(id)
      if (document.visibilityState === 'visible') markRead(id)
    } else {
      activeConversationsRef.current.delete(id)
    }
  }, [markRead])

  const sendFrame = useCallback((frame) => {
    const socket = socketRef.current
    if (socket?.readyState !== WebSocket.OPEN) return false
    socket.send(JSON.stringify(frame))
    return true
  }, [])

  const toggleSound = useCallback(() => {
    setSoundEnabled((enabled) => {
      const next = !enabled
      soundEnabledRef.current = next
      localStorage.setItem(SOUND_KEY, String(next))
      return next
    })
  }, [])

  useEffect(() => {
    if (authStatus !== 'authenticated' || !user?.id) {
      socketRef.current?.close(1000, 'Authentication changed')
      socketRef.current = null
      activeConversationsRef.current.clear()
      unreadRef.current = 0
      setUnreadCount(0)
      setConnection('Mất kết nối')
      return undefined
    }

    let disposed = false
    let retryTimer = null
    let startTimer = null
    let heartbeatTimer = null
    let retryCount = 0
    let socket = null
    const path = user.is_staff || user.is_superuser ? 'admin' : String(user.id)

    const connect = () => {
      if (disposed) return
      setConnection('Đang kết nối')
      socket = new WebSocket(`${backendUrl.replace(/^http/, 'ws')}/ws/chat/${path}/`)
      socketRef.current = socket
      socket.onopen = () => {
        if (disposed || socketRef.current !== socket) return
        retryCount = 0
        setConnection('Đã kết nối')
        window.clearInterval(heartbeatTimer)
        heartbeatTimer = window.setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'ping' }))
        }, 25000)
        syncUnread().catch(() => {})
      }
      socket.onmessage = (event) => {
        if (disposed || socketRef.current !== socket) return
        let frame
        try { frame = JSON.parse(event.data) } catch { return }
        if (frame?.type === 'pong' || frame?.type === 'error') return
        if (frame?.type === 'unread') {
          const conversationId = Number(frame.conversation_id)
          const isVisibleConversation = frame.preview && Number(frame.count) > 0 && conversationId
            && document.visibilityState === 'visible'
            && activeConversationsRef.current.has(conversationId)
          if (isVisibleConversation) {
            markRead(conversationId)
          } else {
            const count = Number(frame.count || 0)
            if (count > unreadRef.current && soundEnabledRef.current) {
              try {
                const AudioContextClass = window.AudioContext || window.webkitAudioContext
                const audio = new AudioContextClass()
                const oscillator = audio.createOscillator()
                const gain = audio.createGain()
                oscillator.frequency.value = 740
                gain.gain.setValueAtTime(0.045, audio.currentTime)
                gain.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + 0.13)
                oscillator.connect(gain)
                gain.connect(audio.destination)
                oscillator.start()
                oscillator.stop(audio.currentTime + 0.13)
                oscillator.onended = () => audio.close()
              } catch { /* Audio is optional and may require browser permission. */ }
            }
            unreadRef.current = count
            setUnreadCount(count)
          }
        }
        if (frame?.type === 'new_message' || frame?.id) {
          window.dispatchEvent(new CustomEvent('travel-chat-frame', { detail: frame }))
        }
      }
      socket.onclose = (event) => {
        if (import.meta.env.DEV) console.info('[chat websocket] closed', { code: event.code, reason: event.reason || '(no reason)' })
        if (disposed || socketRef.current !== socket) return
        window.clearInterval(heartbeatTimer)
        socketRef.current = null
        setConnection('Mất kết nối')
        if ([1000, 1001, 4401, 4403, 4404].includes(event.code)) return
        const delay = Math.min(1000 * (2 ** retryCount), 15000)
        retryCount += 1
        retryTimer = window.setTimeout(connect, delay)
      }
      socket.onerror = () => {
        if (!disposed && socketRef.current === socket) setConnection('Mất kết nối')
      }
    }

    // Deferring the first open lets React StrictMode's setup/cleanup probe cancel
    // the first attempt before it reaches the network.
    startTimer = window.setTimeout(connect, 0)
    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        activeConversationsRef.current.forEach((conversationId) => markRead(conversationId))
      }
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      disposed = true
      window.clearTimeout(startTimer)
      window.clearTimeout(retryTimer)
      window.clearInterval(heartbeatTimer)
      document.removeEventListener('visibilitychange', onVisibility)
      if (socketRef.current === socket) socketRef.current = null
      if (socket && [WebSocket.CONNECTING, WebSocket.OPEN].includes(socket.readyState)) socket.close(1000, 'Chat connection cleanup')
    }
  }, [authStatus, user?.id, user?.is_staff, user?.is_superuser, syncUnread, markRead])

  useEffect(() => {
    if (!previousTitleRef.current) previousTitleRef.current = document.title.replace(/^\(\d+\)\s*/, '')
    document.title = unreadCount > 0 ? `(${unreadCount}) Đi Việt Nam` : previousTitleRef.current
  }, [unreadCount])

  const value = useMemo(() => ({
    connection, unreadCount, syncUnread, markRead, setConversationActive,
    sendFrame, soundEnabled, toggleSound,
  }), [connection, unreadCount, syncUnread, markRead, setConversationActive, sendFrame, soundEnabled, toggleSound])
  return <ChatConnectionContext.Provider value={value}>{children}</ChatConnectionContext.Provider>
}

export function useChatConnection() {
  const context = useContext(ChatConnectionContext)
  if (!context) throw new Error('useChatConnection must be used inside ChatConnectionProvider')
  return context
}
