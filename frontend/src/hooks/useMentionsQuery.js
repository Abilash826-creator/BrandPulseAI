import { useQuery } from '@tanstack/react-query';
import { monitoringAPI, instagramAPI } from '../services/api';

export const useMentionsQuery = (params, activeBrandId) => {
  return useQuery({
    queryKey: ['mentions', activeBrandId, params],
    queryFn: async () => {
      if (!activeBrandId) return { mentions: [], igStatus: null };
      const [mentionsRes, igStatusRes] = await Promise.all([
        monitoringAPI.getMentions({ ...params, brand_id: activeBrandId }),
        instagramAPI.getStatus(activeBrandId).catch(() => ({ data: null }))
      ]);
      return {
        mentions: mentionsRes.data || [],
        igStatus: igStatusRes?.data || null
      };
    },
    enabled: !!activeBrandId,
    staleTime: 15000,
  });
};
