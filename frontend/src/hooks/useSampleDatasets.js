import { useQuery } from '@tanstack/react-query';
import { datasetAPI } from '../services/api';

export const useSampleDatasets = () => {
  return useQuery({
    queryKey: ['sampleDatasets'],
    queryFn: async () => {
      const res = await datasetAPI.getSamples();
      return res.data || [];
    },
    staleTime: 5 * 60 * 1000,
    retry: 1
  });
};
