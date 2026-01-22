import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Login from './pages/Login'
import AdminLayout from './components/Layout/AdminLayout'
import StudentQuery from './pages/Student/StudentQuery'
import Dashboard from './pages/Admin/Dashboard'
import TeacherDashboard from './pages/Teacher/TeacherDashboard'
import Students from './pages/Admin/Students'
import Classes from './pages/Admin/Classes'
import Teachers from './pages/Admin/Teachers'
import Indicators from './pages/Admin/Indicators'
import Semesters from './pages/Admin/Semesters'
import Statistics from './pages/Admin/Statistics'
import TeacherRoleManagement from './pages/Admin/TeacherRoleManagement'
import SystemSettings from './pages/Admin/SystemSettings'
import NoticeManagement from './pages/Admin/NoticeManagement'
import AuditLogViewer from './pages/Admin/AuditLogViewer'
import DataEntry from './pages/Teacher/DataEntry'
import CommentManagement from './pages/Teacher/CommentManagement'
import CalligraphyGrading from './pages/Calligraphy/CalligraphyGrading'
import CalligraphyAssignment from './pages/Calligraphy/CalligraphyAssignment'
import Profile from './pages/Profile/Profile'
import DataScreen from './pages/DataScreen/DataScreen'
import AttendanceManagement from './pages/Attendance/AttendanceManagement'
import ExamManagement from './pages/Exam/ExamManagement'
import ScoreEntry from './pages/Exam/ScoreEntry'
import WrongAnswerAnalysis from './pages/WrongAnswer/WrongAnswerAnalysis'

function App() {
  const { token, user } = useAuthStore()

  // 根据角色决定默认仪表盘
  const getDashboardComponent = () => {
    if (user?.role === 'admin') {
      return <Dashboard />
    } else if (user?.role === 'teacher') {
      return <TeacherDashboard />
    }
    return <TeacherDashboard /> // 默认显示教师工作台
  }

  return (
    <Routes>
      {/* 登录页面 */}
      <Route path="/login" element={<Login />} />

      {/* 学生查询页面（无需登录） */}
      <Route path="/student" element={<StudentQuery />} />

      {/* 数据大屏（无需登录，独立全屏） */}
      <Route path="/data-screen" element={<DataScreen />} />

      {/* 管理后台（需要登录） */}
      <Route
        path="/*"
        element={
          token ? (
            <AdminLayout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />

                {/* 仪表盘 - 根据角色显示不同内容 */}
                <Route path="/dashboard" element={getDashboardComponent()} />

                {/* 个人资料 - 所有登录用户都可访问 */}
                <Route path="/profile" element={<Profile />} />

                {/* 管理员功能 */}
                {user?.role === 'admin' && (
                  <>
                    <Route path="/semesters" element={<Semesters />} />
                    <Route path="/classes" element={<Classes />} />
                    <Route path="/students" element={<Students />} />
                    <Route path="/teachers" element={<Teachers />} />
                    <Route path="/indicators" element={<Indicators />} />
                    <Route path="/statistics" element={<Statistics />} />
                    <Route path="/exam-management" element={<ExamManagement />} />
                    <Route path="/teacher-roles" element={<TeacherRoleManagement />} />
                    <Route path="/system-settings" element={<SystemSettings />} />
                    <Route path="/notices" element={<NoticeManagement />} />
                    <Route path="/audit-logs" element={<AuditLogViewer />} />
                  </>
                )}

                {/* 教师功能 */}
                {(user?.role === 'teacher' || user?.role === 'admin') && (
                  <>
                    <Route path="/data-entry" element={<DataEntry />} />
                    <Route path="/comment-management" element={<CommentManagement />} />
                    <Route path="/calligraphy" element={<CalligraphyGrading />} />
                    <Route path="/calligraphy-assignment" element={<CalligraphyAssignment />} />
                    <Route path="/attendance" element={<AttendanceManagement />} />
                    <Route path="/score-entry" element={<ScoreEntry />} />
                    <Route path="/wrong-answer" element={<WrongAnswerAnalysis />} />
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




