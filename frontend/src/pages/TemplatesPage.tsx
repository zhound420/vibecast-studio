import { FileText } from 'lucide-react'

export function TemplatesPage() {
  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Templates</h1>
          <p className="text-slate-400 mt-1">
            Pre-configured templates for common audio formats
          </p>
        </div>

        <div className="text-center py-16">
          <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h2 className="text-xl font-medium text-white mb-2">Coming Soon</h2>
          <p className="text-slate-400">
            Templates for podcasts, interviews, and narration will be available here.
          </p>
        </div>
      </div>
    </div>
  )
}
