import { useQuery } from '@tanstack/react-query';
import { mlAPI } from '../services/api';

export const useModelMetrics = () => {
  return useQuery({
    queryKey: ['model_metrics'],
    queryFn: async () => {
      const [dataRes, metricsRes] = await Promise.all([
        mlAPI.getDatasetInfo(),
        mlAPI.getMetrics()
      ]);
      return {
        datasetInfo: dataRes.data,
        metrics: metricsRes.data
      };
    },
    staleTime: 60000,
  });
};
