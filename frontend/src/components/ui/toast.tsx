import React, { createContext, useContext, useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

// Toast types
export interface Toast {
  id: string
  title?: string
  description?: string
  type?: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  action?: React.ReactNode
}

interface ToastContextType {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
  removeAllToasts: () => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

// Toast Provider Component
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 15)
    const newToast = {
      ...toast,
      id,
      duration: toast.duration ?? 5000,
    }
    
    setToasts(prev => [...prev, newToast])

    // Auto remove after duration
    if (newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, newToast.duration)
    }
  }

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }

  const removeAllToasts = () => {
    setToasts([])
  }

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, removeAllToasts }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  )
}

// Toast Container Component
function ToastContainer() {
  const context = useContext(ToastContext)
  if (!context) return null

  const { toasts } = context

  if (typeof window === 'undefined') return null

  return createPortal(
    <div className="fixed top-4 right-4 z-50 flex flex-col space-y-2 max-w-sm">
      {toasts.map(toast => (
        <ToastComponent key={toast.id} toast={toast} />
      ))}
    </div>,
    document.body
  )
}

// Individual Toast Component
function ToastComponent({ toast }: { toast: Toast }) {
  const context = useContext(ToastContext)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    setIsVisible(true)
  }, [])

  const handleClose = () => {
    setIsVisible(false)
    setTimeout(() => {
      context?.removeToast(toast.id)
    }, 150)
  }

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  }

  const Icon = icons[toast.type || 'info']

  const colorClasses = {
    success: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-950 dark:border-green-800 dark:text-green-200',
    error: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-950 dark:border-red-800 dark:text-red-200',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-950 dark:border-yellow-800 dark:text-yellow-200',
    info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-950 dark:border-blue-800 dark:text-blue-200',
  }

  const iconColorClasses = {
    success: 'text-green-500',
    error: 'text-red-500',
    warning: 'text-yellow-500',
    info: 'text-blue-500',
  }

  return (
    <div
      className={cn(
        'relative flex items-start space-x-3 p-4 border rounded-lg shadow-lg transition-all duration-150 transform',
        colorClasses[toast.type || 'info'],
        isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
      )}
    >
      <Icon className={cn('w-5 h-5 flex-shrink-0 mt-0.5', iconColorClasses[toast.type || 'info'])} />
      
      <div className="flex-1 min-w-0">
        {toast.title && (
          <p className="text-sm font-semibold">{toast.title}</p>
        )}
        {toast.description && (
          <p className="text-sm mt-1">{toast.description}</p>
        )}
        {toast.action && (
          <div className="mt-2">{toast.action}</div>
        )}
      </div>

      <button
        onClick={handleClose}
        className="flex-shrink-0 ml-4 text-gray-400 hover:text-gray-600 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

// Hook to use toast
export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

// Utility functions for common toast types
export const toast = {
  success: (message: string, title?: string, options?: Partial<Toast>) => {
    const context = useContext(ToastContext)
    context?.addToast({
      type: 'success',
      title,
      description: message,
      ...options,
    })
  },
  error: (message: string, title?: string, options?: Partial<Toast>) => {
    const context = useContext(ToastContext)
    context?.addToast({
      type: 'error',
      title,
      description: message,
      duration: 7000, // Longer duration for errors
      ...options,
    })
  },
  warning: (message: string, title?: string, options?: Partial<Toast>) => {
    const context = useContext(ToastContext)
    context?.addToast({
      type: 'warning',
      title,
      description: message,
      ...options,
    })
  },
  info: (message: string, title?: string, options?: Partial<Toast>) => {
    const context = useContext(ToastContext)
    context?.addToast({
      type: 'info',
      title,
      description: message,
      ...options,
    })
  },
}
