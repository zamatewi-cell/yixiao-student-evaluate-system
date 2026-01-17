import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Login from './pages/Login'
import AdminLayout from './components/Layout/AdminLayout'
import StudentQuery from './pages/Student/StudentQuery'
import Dashboard from './pages/Admin/Dashboard'
import Students from './pages/Admin/Students'
import Classes from './pages/Admin/Classes'
import Teachers from './pages/Admin/Teachers'
import Indicators from './pages/Admin/Indicators'
import Semesters from './pages/Admin/Semesters'
import Statistics from './pages/Admin/Statistics'
import DataEntry from './pages/Teacher/DataEntry'
import CommentManagement from './pages/Teacher/CommentManagement'
import CalligraphyGrading from './pages/Calligraphy/CalligraphyGrading'

function App() {
  const { token, user } = useAuthStore()

  return (
    <Routes>
      {/* 登录页面 */}
      <Route path="/login" element={<Login />} />

      {/* 学生查询页面（无需登录） */}
      <Route path="/student" element={<StudentQuery />} />

      {/* 管理后台（需要登录） */}
      <Route
        path="/*"
        element={
          token ? (
            <AdminLayout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />

                {/* 管理员功能 */}
                {user?.role === 'admin' && (
                  <>
                    <Route path="/semesters" element={<Semesters />} />
                    <Route path="/classes" element={<Classes />} />
                    <Route path="/students" element={<Students />} />
                    <Route path="/teachers" element={<Teachers />} />
                    <Route path="/indicators" element={<Indicators />} />
                    <Route path="/statistics" element={<Statistics />} />
                  </>
                )}

                {/* 教师功能 */}
                {(user?.role === 'teacher' || user?.role === 'admin') && (
                  <>
                    <Route path="/data-entry" element={<DataEntry />} />
                    <Route path="/comment-management" element={<CommentManagement />} />
                    <Route path="/calligraphy" element={<CalligraphyGrading />} />
                  </>
                )}

                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </AdminLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
    </Routes>
  )
}

export default App
