import { Routes, Route } from 'react-router-dom'
import { Header } from './components/Header'
import { Footer } from './components/Footer'
import { LandingPage } from './pages/LandingPage'
import { ExplorePage } from './pages/ExplorePage'
import { WorkoutDetailPage } from './pages/WorkoutDetailPage'
import { ExercisesPage } from './pages/ExercisesPage'
import { ExerciseDetailPage } from './pages/ExerciseDetailPage'
import { DocsPage } from './pages/DocsPage'

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/explore" element={<ExplorePage />} />
          <Route path="/workout/:slug" element={<WorkoutDetailPage />} />
          <Route path="/exercises" element={<ExercisesPage />} />
          <Route path="/exercise/:slug" element={<ExerciseDetailPage />} />
          <Route path="/docs" element={<DocsPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}

export default App
