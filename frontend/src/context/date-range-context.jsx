import React, { createContext, useContext, useState } from 'react';

const DateRangeContext = createContext();

const todayStart = (() => {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
})();
const todayEnd = (() => {
  const d = new Date();
  d.setHours(23, 59, 59, 999);
  return d;
})();

export const DateRangeProvider = ({ children }) => {
  const [startDate, setStartDate] = useState(todayStart);
  const [endDate, setEndDate] = useState(todayEnd);
  const [loading, setLoading] = useState(false);
  const [cache, setCache] = useState(() => {
    const cached = localStorage.getItem('dataCache');
    return cached ? JSON.parse(cached) : {};
  });

  return (
    <DateRangeContext.Provider value={{ startDate, setStartDate, endDate, setEndDate, loading, setLoading, cache, setCache }}>
      {children}
    </DateRangeContext.Provider>
  );
};

export const useDateRange = () => useContext(DateRangeContext); 