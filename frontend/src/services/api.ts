import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  getMe: () => api.get('/auth/me'),
  changePassword: (oldPassword: string, newPassword: string) =>
    api.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
}

// Admin API
export const adminApi = {
  // Users
  getUsers: (params?: any) => api.get('/admin/users', { params }),
  createUser: (data: any) => api.post('/admin/users', data),
  updateUser: (id: number, data: any) => api.put(`/admin/users/${id}`, data),
  deleteUser: (id: number) => api.delete(`/admin/users/${id}`),
  
  // Semesters
  getSemesters: () => api.get('/admin/semesters'),
  createSemester: (data: any) => api.post('/admin/semesters', data),
  setCurrentSemester: (id: number) => api.put(`/admin/semesters/${id}/set-current`),
  
  // Grades
  getGrades: () => api.get('/admin/grades'),
  
  // Classes
  getClasses: (gradeId?: number) => api.get('/admin/classes', { params: { grade_id: gradeId } }),
  createClass: (data: any) => api.post('/admin/classes', data),
  
  // Students
  getStudents: (params?: any) => api.get('/admin/students', { params }),
  createStudent: (data: any) => api.post('/admin/students', data),
  getStudentBarcode: (id: number) => api.get(`/admin/students/${id}/barcode`),
  
  // Teachers
  getTeachers: () => api.get('/admin/teachers'),
  createTeacher: (data: any) => api.post('/admin/teachers', data),
  
  // Indicators
  getIndicatorCategories: () => api.get('/admin/indicator-categories'),
  getIndicators: (categoryId?: number) => api.get('/admin/indicators', { params: { category_id: categoryId } }),
  createIndicator: (data: any) => api.post('/admin/indicators', data),
}

// Teacher API
export const teacherApi = {
  getProfile: () => api.get('/teacher/profile'),
  getMyClasses: () => api.get('/teacher/my-classes'),
  getClassStudents: (classId: number) => api.get(`/teacher/classes/${classId}/students`),
  getCurrentSemester: () => api.get('/teacher/current-semester'),
  createEvaluation: (data: any) => api.post('/teacher/evaluations', data),
  batchCreateEvaluations: (data: any) => api.post('/teacher/evaluations/batch', data),
  getClassEvaluations: (classId: number, semesterId: number, indicatorId?: number) =>
    api.get(`/teacher/classes/${classId}/evaluations`, { params: { semester_id: semesterId, indicator_id: indicatorId } }),
  getCalligraphyRecords: (params?: any) => api.get('/teacher/calligraphy-records', { params }),
}

// Student API
export const studentApi = {
  simpleLogin: (studentNo: string, name: string) =>
    api.post('/student/simple-login', { student_no: studentNo, name }),
  getEvaluations: (studentId: number, semesterId?: number) =>
    api.get(`/student/evaluations/${studentId}`, { params: { semester_id: semesterId } }),
  getRadar: (studentId: number, semesterId?: number) =>
    api.get(`/student/radar/${studentId}`, { params: { semester_id: semesterId } }),
  getCalligraphy: (studentId: number, params?: any) =>
    api.get(`/student/calligraphy/${studentId}`, { params }),
  getComments: (studentId: number, semesterId?: number) =>
    api.get(`/student/comments/${studentId}`, { params: { semester_id: semesterId } }),
}

// Statistics API
export const statisticsApi = {
  getStudentStats: (studentId: number, semesterId?: number) =>
    api.get(`/statistics/student/${studentId}`, { params: { semester_id: semesterId } }),
  getClassStats: (classId: number, semesterId?: number) =>
    api.get(`/statistics/class/${classId}`, { params: { semester_id: semesterId } }),
  getGradeStats: (gradeId: number, semesterId?: number) =>
    api.get(`/statistics/grade/${gradeId}`, { params: { semester_id: semesterId } }),
  getSchoolStats: (semesterId?: number) =>
    api.get('/statistics/school', { params: { semester_id: semesterId } }),
}

// Upload API
export const uploadApi = {
  uploadImage: (file: File, useAi: boolean = true) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/upload?use_ai=${useAi}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getRecords: (params?: any) => api.get('/records', { params }),
  getRecord: (id: number) => api.get(`/records/${id}`),
  deleteRecord: (id: number) => api.delete(`/records/${id}`),
  getStats: () => api.get('/stats'),
}

export default api
