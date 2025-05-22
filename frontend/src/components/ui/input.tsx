import * as React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = 'Input'

// Number Input with validation
export interface NumberInputProps extends Omit<InputProps, 'type' | 'value' | 'onChange'> {
  value?: number
  onChange?: (value: number) => void
  min?: number
  max?: number
  step?: number
  precision?: number
}

const NumberInput = React.forwardRef<HTMLInputElement, NumberInputProps>(
  ({ className, value, onChange, min, max, step = 1, precision = 2, ...props }, ref) => {
    const [displayValue, setDisplayValue] = React.useState(value?.toString() || '')

    React.useEffect(() => {
      setDisplayValue(value?.toString() || '')
    }, [value])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const inputValue = e.target.value
      setDisplayValue(inputValue)

      const numValue = parseFloat(inputValue)
      if (!isNaN(numValue)) {
        const clampedValue = Math.min(Math.max(numValue, min || -Infinity), max || Infinity)
        const preciseValue = parseFloat(clampedValue.toFixed(precision))
        onChange?.(preciseValue)
      }
    }

    const handleBlur = () => {
      if (value !== undefined) {
        setDisplayValue(value.toString())
      }
    }

    return (
      <Input
        ref={ref}
        type="number"
        className={cn('font-mono', className)}
        value={displayValue}
        onChange={handleChange}
        onBlur={handleBlur}
        min={min}
        max={max}
        step={step}
        {...props}
      />
    )
  }
)
NumberInput.displayName = 'NumberInput'

// Password Input with visibility toggle
export interface PasswordInputProps extends Omit<InputProps, 'type'> {
  showToggle?: boolean
}

const PasswordInput = React.forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ className, showToggle = true, ...props }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false)

    return (
      <div className="relative">
        <Input
          ref={ref}
          type={showPassword ? 'text' : 'password'}
          className={cn('pr-10', className)}
          {...props}
        />
        {showToggle && (
          <button
            type="button"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? (
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
              </svg>
            )}
          </button>
        )}
      </div>
    )
  }
)
PasswordInput.displayName = 'PasswordInput'

export { Input, NumberInput, PasswordInput }
