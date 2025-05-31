export function calculateEngagementRate(metrics: {
  likes: number
  comments: number
  shares: number
  views: number
}) {
  const totalEngagement = metrics.likes + metrics.comments + metrics.shares
  return metrics.views > 0 ? totalEngagement / metrics.views : 0
}

export function calculateGrowthRate(current: number, previous: number) {
  if (previous === 0) return current > 0 ? 1 : 0
  return (current - previous) / previous
}

export function getPerformanceGrade(score: number) {
  if (score >= 90) return { grade: 'A+', color: 'text-ml-green-600' }
  if (score >= 80) return { grade: 'A', color: 'text-ml-green-600' }
  if (score >= 70) return { grade: 'B', color: 'text-prediction-600' }
  if (score >= 60) return { grade: 'C', color: 'text-orange-600' }
  return { grade: 'D', color: 'text-red-600' }
}

export function calculateConfidenceInterval(value: number, confidence: number = 0.95) {
  const margin = value * (1 - confidence) * 0.5
  return {
    lower: Math.max(0, value - margin),
    upper: value + margin
  }
}

export function detectTrend(data: number[]) {
  if (data.length < 2) return 'stable'
  
  const recentData = data.slice(-5) // Last 5 data points
  const firstHalf = recentData.slice(0, Math.floor(recentData.length / 2))
  const secondHalf = recentData.slice(Math.floor(recentData.length / 2))
  
  const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length
  const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length
  
  const changePercent = (secondAvg - firstAvg) / firstAvg
  
  if (changePercent > 0.1) return 'increasing'
  if (changePercent < -0.1) return 'decreasing'
  return 'stable'
}

export function groupByTimeframe(
  data: Array<{ timestamp: string; value: number }>,
  timeframe: 'day' | 'week' | 'month'
) {
  const grouped = new Map()
  
  data.forEach(item => {
    const date = new Date(item.timestamp)
    let key: string
    
    switch (timeframe) {
      case 'day':
        key = date.toISOString().split('T')[0]
        break
      case 'week':
        const weekStart = new Date(date)
        weekStart.setDate(date.getDate() - date.getDay())
        key = weekStart.toISOString().split('T')[0]
        break
      case 'month':
        key = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`
        break
    }
    
    if (!grouped.has(key)) {
      grouped.set(key, [])
    }
    grouped.get(key).push(item.value)
  })
  
  return Array.from(grouped.entries()).map(([key, values]) => ({
    period: key,
    value: values.reduce((a: number, b: number) => a + b, 0) / values.length,
    count: values.length
  }))
}
