import React, { createContext, useContext, useState, useEffect } from 'react';
import { brandsAPI } from '../services/api';
import { useAuth } from './AuthContext';

const BrandContext = createContext(null);

export const BrandProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [brands, setBrands] = useState([]);
  const [activeBrand, setActiveBrand] = useState(null);
  const [loading, setLoading] = useState(false);
  const [simulationScenario, setSimulationScenario] = useState('normal'); // normal, crisis, viral_launch, competitor_attack

  const fetchBrands = async (preferredBrandId = null) => {
    if (!isAuthenticated) return [];
    setLoading(true);
    try {
      const res = await brandsAPI.list();
      const list = res.data || [];
      setBrands(list);
      if (list.length > 0) {
        let selected = null;
        if (preferredBrandId) {
          selected = list.find(b => b.id === preferredBrandId);
        }
        if (!selected && activeBrand) {
          selected = list.find(b => b.id === activeBrand.id);
        }
        if (!selected) {
          selected = list.find(b => b.is_primary) || list[0];
        }
        setActiveBrand(selected);
        return list;
      }
      return [];
    } catch (err) {
      console.error("Failed to load brands:", err);
      return [];
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBrands();
  }, [isAuthenticated]);

  const createBrand = async (brandData) => {
    const res = await brandsAPI.create(brandData);
    const newBrand = res.data;
    setBrands(prev => [newBrand, ...prev]);
    setActiveBrand(newBrand);
    return newBrand;
  };

  const deleteBrand = async (brandId) => {
    try {
      await brandsAPI.delete(brandId);
      setBrands(prev => {
        const updated = prev.filter(b => b.id !== brandId);
        if (activeBrand?.id === brandId) {
          setActiveBrand(updated.length > 0 ? (updated.find(b => b.is_primary) || updated[0]) : null);
        }
        return updated;
      });
      return true;
    } catch (err) {
      console.error("Failed to delete brand:", err);
      throw err;
    }
  };

  const selectBrandById = (brandId) => {
    const found = brands.find(b => b.id === brandId);
    if (found) {
      setActiveBrand(found);
    } else {
      fetchBrands(brandId);
    }
  };

  const [selectedLocationId, setSelectedLocationId] = useState('all');

  const addLocation = async (brandId, locationData) => {
    const res = await brandsAPI.addLocation(brandId, locationData);
    const updatedBrand = res.data;
    setBrands(prev => prev.map(b => b.id === brandId ? updatedBrand : b));
    if (activeBrand?.id === brandId) setActiveBrand(updatedBrand);
    return updatedBrand;
  };

  const updateLocation = async (brandId, locationId, locationData) => {
    const res = await brandsAPI.updateLocation(brandId, locationId, locationData);
    const updatedBrand = res.data;
    setBrands(prev => prev.map(b => b.id === brandId ? updatedBrand : b));
    if (activeBrand?.id === brandId) setActiveBrand(updatedBrand);
    return updatedBrand;
  };

  const deleteLocation = async (brandId, locationId) => {
    const res = await brandsAPI.deleteLocation(brandId, locationId);
    const updatedBrand = res.data;
    setBrands(prev => prev.map(b => b.id === brandId ? updatedBrand : b));
    if (activeBrand?.id === brandId) setActiveBrand(updatedBrand);
    return updatedBrand;
  };

  return (
    <BrandContext.Provider value={{
      brands,
      businesses: brands,
      activeBrand,
      activeBusiness: activeBrand,
      setActiveBrand,
      setActiveBusiness: setActiveBrand,
      selectBrandById,
      selectBusinessById: selectBrandById,
      selectedLocationId,
      setSelectedLocationId,
      addLocation,
      updateLocation,
      deleteLocation,
      loading,
      refreshBrands: fetchBrands,
      refreshBusinesses: fetchBrands,
      createBrand,
      createBusiness: createBrand,
      deleteBrand,
      deleteBusiness: deleteBrand,
      simulationScenario,
      setSimulationScenario
    }}>
      {children}
    </BrandContext.Provider>
  );
};

export const useBrand = () => useContext(BrandContext);
export const useBusiness = useBrand;
