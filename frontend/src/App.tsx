import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Landing } from './pages/Landing'
import { Studio } from './pages/Studio'

function ProjectToStudioRedirect() {
  const { projectId } = useParams()
  return <Navigate to={`/studio/${projectId}`} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Landing />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="studio/:projectId" element={<Studio />} />
          <Route path="projects/:projectId" element={<ProjectToStudioRedirect />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
