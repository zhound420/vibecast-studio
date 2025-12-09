import clsx from 'clsx'

interface ProgressBarProps {
  progress: number
  size?: 'sm' | 'md' | 'lg'
  variant?: 'primary' | 'success' | 'warning' | 'danger'
  showLabel?: boolean
  className?: string
}

export function ProgressBar({
  progress,
  size = 'md',
  variant = 'primary',
  showLabel = false,
  className,
}: ProgressBarProps) {
  const sizes = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-4',
  }

  const variants = {
    primary: 'bg-primary-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    danger: 'bg-red-500',
  }

  const clampedProgress = Math.min(100, Math.max(0, progress))

  return (
    <div className={clsx('w-full', className)}>
      <div className={clsx('w-full bg-slate-700 rounded-full overflow-hidden', sizes[size])}>
        <div
          className={clsx('h-full rounded-full transition-all duration-300', variants[variant])}
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
      {showLabel && (
        <div className="mt-1 text-sm text-slate-400 text-right">
          {clampedProgress.toFixed(0)}%
        </div>
      )}
    </div>
  )
}
