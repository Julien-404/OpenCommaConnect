import React, { useEffect, useState } from 'react';
import { devicesAPI, routesAPI } from '../services/api';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const [devices, setDevices] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [devicesRes, routesRes] = await Promise.all([
          devicesAPI.list(),
          routesAPI.list(1, 10),
        ]);

        setDevices(devicesRes.data);
        setRoutes(routesRes.data.routes);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      <div className="dashboard-grid">
        <div className="card">
          <h3>Devices</h3>
          <div className="stat-value">{devices.length}</div>
          <p>Connected devices</p>
        </div>

        <div className="card">
          <h3>Routes</h3>
          <div className="stat-value">{routes.length}</div>
          <p>Recent routes</p>
        </div>

        <div className="card">
          <h3>Total Distance</h3>
          <div className="stat-value">0 km</div>
          <p>This month</p>
        </div>

        <div className="card">
          <h3>Driving Time</h3>
          <div className="stat-value">0 hrs</div>
          <p>This month</p>
        </div>
      </div>

      <div className="recent-routes">
        <h2>Recent Routes</h2>
        {routes.length === 0 ? (
          <p>No routes yet</p>
        ) : (
          <div className="routes-list">
            {routes.map((route: any) => (
              <div key={route.id} className="route-item card">
                <h4>{route.fullname}</h4>
                <p>Start: {new Date(route.start_time).toLocaleString()}</p>
                {route.distance_meters && (
                  <p>Distance: {(route.distance_meters / 1000).toFixed(2)} km</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
