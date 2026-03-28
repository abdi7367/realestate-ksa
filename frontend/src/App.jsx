import { ConfigProvider, theme } from 'antd'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AppLayout } from './components/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { PropertiesPage } from './pages/PropertiesPage'
import { ReportsPage } from './pages/ReportsPage'
import { ContractsPage } from './pages/ContractsPage'
import { DebtsPage } from './pages/DebtsPage'
import { FinancePage } from './pages/FinancePage'
import { VouchersPage } from './pages/VouchersPage'

export default function App() {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
      }}
    >
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<DashboardPage />} />
              <Route path="/properties" element={<PropertiesPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/contracts" element={<ContractsPage />} />
              <Route path="/debts" element={<DebtsPage />} />
              <Route path="/finance" element={<FinancePage />} />
              <Route path="/vouchers" element={<VouchersPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ConfigProvider>
  )
}
