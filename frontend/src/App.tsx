import { Routes, Route } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { Dashboard } from './pages/Dashboard'
import { ProjectPage } from './pages/ProjectPage'
import { VoicesPage } from './pages/VoicesPage'
import { TemplatesPage } from './pages/TemplatesPage'
import { SettingsPage } from './pages/SettingsPage'

function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/project/:projectId" element={<ProjectPage />} />
        <Route path="/voices" element={<VoicesPage />} />
        <Route path="/templates" element={<TemplatesPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </AppLayout>
  )
}

export default App
