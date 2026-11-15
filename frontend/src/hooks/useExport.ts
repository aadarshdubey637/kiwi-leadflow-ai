import { useState } from 'react'
import { toast } from 'sonner'
import { errorMessage } from '@/api/axiosInstance'
import { enquiryApi } from '@/api/enquiryApi'
import type { EnquiryFilters } from '@/types/api'

/** Downloads GET /api/enquiries/export as CSV or Excel (a protected endpoint, so it must go through axios with the token). */
export function useExport() {
  const [exporting, setExporting] = useState<'csv' | 'xlsx' | null>(null)

  const exportFile = async (format: 'csv' | 'xlsx', filters: Omit<EnquiryFilters, 'page' | 'page_size'> = {}) => {
    setExporting(format)
    try {
      const blob = await enquiryApi.exportFile(format, filters)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `enquiries-${new Date().toISOString().slice(0, 10)}.${format}`
      a.click()
      URL.revokeObjectURL(url)
      toast.success(format === 'xlsx' ? 'Excel file exported' : 'CSV exported')
    } catch (e) {
      toast.error(errorMessage(e))
    } finally {
      setExporting(null)
    }
  }
  return { exportFile, exporting }
}

/** Kept for existing callers. */
export const useCsvExport = () => {
  const { exportFile, exporting } = useExport()
  return { exportCsv: (f: Omit<EnquiryFilters, 'page' | 'page_size'> = {}) => exportFile('csv', f), exporting: exporting === 'csv' }
}
