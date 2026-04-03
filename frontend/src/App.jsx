import { App as AntApp, ConfigProvider, theme } from 'antd'
import arEG from 'antd/locale/ar_EG'
import enUS from 'antd/locale/en_US'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AppLayout } from './components/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { PropertiesPage } from './pages/PropertiesPage'
import { PropertyDetailPage } from './pages/PropertyDetailPage'
import { ReportsPage } from './pages/ReportsPage'
import { ContractsPage } from './pages/ContractsPage'
import { DebtsPage } from './pages/DebtsPage'
import { FinancePage } from './pages/FinancePage'
import { VouchersPage } from './pages/VouchersPage'

function AppRoutes() {
  return (
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
          <Route path="/properties/:id" element={<PropertyDetailPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/contracts" element={<ContractsPage />} />
          <Route path="/debts" element={<DebtsPage />} />
          <Route path="/finance" element={<FinancePage />} />
          <Route path="/vouchers" element={<VouchersPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

function AppWithTheme() {
  const { i18n } = useTranslation()
  const isAr = i18n.language === 'ar'

  return (
    <ConfigProvider
      direction={isAr ? 'rtl' : 'ltr'}
      locale={isAr ? arEG : enUS}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#0d9488',
          borderRadiusLG: 12,
        },
      }}
    >
      <AntApp>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </AntApp>
    </ConfigProvider>
  )
}

export default function App() {
  return <AppWithTheme />
}
