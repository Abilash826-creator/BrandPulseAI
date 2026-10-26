import { useQuery } from '@tanstack/react-query';
import { analyticsAPI, monitoringAPI, crisisAPI, instagramAPI, competitorsAPI } from '../services/api';

export const useDashboardData = (activeBrandId, timeRange = '7d', dataFilter = 'all') => {
  return useQuery({
    queryKey: ['dashboard', activeBrandId, timeRange, dataFilter],
    queryFn: async () => {
      if (!activeBrandId) return null;
      const simFilter = dataFilter === 'all' ? undefined : (dataFilter === 'simulated');

      const [
        overviewRes,
        trendsRes,
        emotionsRes,
        mentionsRes,
        alertsRes,
        insightsRes,
        igMetricsRes,
        sovResponse
      ] = await Promise.all([
        analyticsAPI.getOverview(activeBrandId, timeRange, simFilter),
        analyticsAPI.getTrends(activeBrandId, timeRange, simFilter),
        analyticsAPI.getEmotions(activeBrandId),
        monitoringAPI.getMentions({ brand_id: activeBrandId, limit: 10, is_simulated: simFilter }),
        crisisAPI.getAlerts(activeBrandId, 'all', simFilter),
        analyticsAPI.getInsights(activeBrandId),
        instagramAPI.getMetrics(activeBrandId).catch(() => ({ data: null })),
        competitorsAPI.getSOV(activeBrandId).catch(() => ({ data: { share_of_voice: [] } }))
      ]);

      return {
        overview: overviewRes.data,
        trends: trendsRes.data,
        emotions: emotionsRes.data,
        mentions: mentionsRes.data,
        alerts: alertsRes.data,
        insights: insightsRes.data,
        igMetrics: igMetricsRes?.data || null,
        sovData: sovResponse.data?.share_of_voice || []
      };
    },
    enabled: !!activeBrandId,
    staleTime: 30000,
  });
};
