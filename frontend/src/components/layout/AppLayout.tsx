import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Home, Mic2, FileText, Settings, AudioWaveform } from 'lucide-react'
import clsx from 'clsx'

interface AppLayoutProps {
  children: ReactNode
}

const navItems = [
  { path: '/', icon: Home, label: 'Dashboard' },
  { path: '/voices', icon: Mic2, label: 'Voices' },
  { path: '/templates', icon: FileText, label: 'Templates' },
  { path: '/settings', icon: Settings, label: 'Settings' },
]

export function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation()

  return (
    <div className="flex h-screen bg-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b border-slate-700">
          <Link to="/" className="flex items-center gap-2 text-white">
            <AudioWaveform className="w-8 h-8 text-primary-500" />
            <span className="font-bold text-xl">VibeCast Studio</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={clsx(
                      'flex items-center gap-3 px-4 py-2 rounded-lg transition-colors',
                      isActive
                        ? 'bg-primary-600 text-white'
                        : 'text-slate-400 hover:bg-slate-700 hover:text-white'
                    )}
                  >
                    <item.icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-700 text-slate-500 text-sm">
          <p>Powered by VibeVoice</p>
          <p className="text-xs mt-1">AI-Generated Content</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
