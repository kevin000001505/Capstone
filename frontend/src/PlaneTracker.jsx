import React, { useState, useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchPlanes, fetchDRAP } from './api/api';

// leaflet.heat requires the global L to exist.
// We import our setup shim first (it sets window.L = L),
// then import leaflet.heat which reads L from global scope.
import './leaflet-heat-setup';
import 'leaflet.heat';

// Component that renders DRAP data as a heatmap layer
const HeatmapLayer = ({ points }) => {
  const map = useMap();
  const heatLayerRef = useRef(null);

  useEffect(() => {
    if (!map) return;

    // Remove existing heat layer
    if (heatLayerRef.current) {
      map.removeLayer(heatLayerRef.current);
      heatLayerRef.current = null;
    }

    if (!points || points.length === 0) return;

    // points are [lat, lon, intensity]
    const heatPoints = points.map(([lat, lon, intensity]) => [lat, lon, intensity]);

    heatLayerRef.current = L.heatLayer(heatPoints, {
      radius: 20,
      blur: 30,
      maxZoom: 10,
      max: 1.0,
      minOpacity: 0.3,
      gradient: {
        0.0: 'blue',
        0.2: 'cyan',
        0.4: 'lime',
        0.6: 'yellow',
        0.8: 'orange',
        1.0: 'red'
      }
    }).addTo(map);

    return () => {
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current);
        heatLayerRef.current = null;
      }
    };
  }, [map, points]);

  return null;
};

const createPlaneIcon = (heading, altitude) => {
  const color = altitude > 36000 ? '#ff6b6b' : altitude > 30000 ? '#ffa500' : '#4ecdc4';
  
  return L.divIcon({
    className: 'custom-plane-icon',
    html: `
      <div style="transform: rotate(${heading}deg); width: 30px; height: 30px;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${color}">
          <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
        </svg>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  });
};

  const PlaneTracker = () => {
  const dispatch = useDispatch();
  const { data: planes, loading: planesLoading, error: planesError } = useSelector((state) => state.planes);
  const { points: drapPoints, loading: drapLoading, error: drapError } = useSelector((state) => state.drap);
  
  const [selectedPlane, setSelectedPlane] = useState(null);
  const [filter, setFilter] = useState('all');
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // Fetch data on component mount
    dispatch(fetchPlanes());
    dispatch(fetchDRAP());

    // Set up interval to refresh data every 2 minutes
    const interval = setInterval(() => {
      dispatch(fetchPlanes());
      dispatch(fetchDRAP());
    }, 120000);

    return () => clearInterval(interval);
  }, [dispatch]);

  const getFilteredPlanes = () => {
    if (!planes || planes.length === 0) return [];
    
    switch (filter) {
      case 'high':
        return planes.filter(p => p.geo_altitude && p.geo_altitude > 36000);
      case 'medium':
        return planes.filter(p => p.geo_altitude && p.geo_altitude >= 30000 && p.geo_altitude <= 36000);
      case 'low':
        return planes.filter(p => p.geo_altitude && p.geo_altitude < 30000);
      default:
        return planes.filter(p => p.lat && p.lon); // Only show planes with valid coordinates
    }
  };

  const filteredPlanes = getFilteredPlanes();

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', display: 'flex' }}>
      <MapContainer
        center={[30, 0]}
        zoom={3}
        minZoom={2}
        style={{ width: '100%', height: '100%', flex: 1 }}
        zoomControl={true}
        scrollWheelZoom={true}
        worldCopyJump={true}
        maxBounds={[[-90, -Infinity], [90, Infinity]]}
        maxBoundsViscosity={1.0}
      >

        {darkMode ? (
          <TileLayer
            attribution='&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>'
            url="https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png"
            noWrap={false}
          />
        ) : (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            noWrap={false}
          />
        )}

        {/* Render DRAP heatmap */}
        {drapPoints && drapPoints.length > 0 && <HeatmapLayer points={drapPoints} />}

        {/* Render planes */}
        {filteredPlanes.map((plane) => (
          <Marker
            key={plane.icao24}
            position={[plane.lat, plane.lon]}
            icon={createPlaneIcon(plane.heading || 0, plane.geo_altitude || 0)}
            eventHandlers={{
              click: () => setSelectedPlane(plane),
            }}
          >
            <Popup>
              <div style={{ padding: '8px', minWidth: '180px' }}>
                <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>
                  {plane.callsign || plane.icao24}
                </h3>
                <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                  <strong>ICAO24:</strong> {plane.icao24}<br/>
                  <strong>Altitude:</strong> {plane.geo_altitude ? plane.geo_altitude.toLocaleString() : 'N/A'} ft<br/>
                  <strong>Speed:</strong> {plane.velocity ? plane.velocity.toFixed(1) : 'N/A'} knots<br/>
                  <strong>Heading:</strong> {plane.heading ? Math.round(plane.heading) : 'N/A'}°<br/>
                  <strong>On Ground:</strong> {plane.on_ground ? 'Yes' : 'No'}<br/>
                  <strong>Position:</strong><br/>
                  {plane.lat.toFixed(4)}°, {plane.lon.toFixed(4)}°
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Filter Controls */}
      <div style={{
        position: 'absolute',
        left: '10px',
        top: '10px',
        zIndex: 1000,
        backgroundColor: 'white',
        padding: '10px',
        borderRadius: '4px',
        boxShadow: '0 1px 5px rgba(0,0,0,0.4)',
      }}>
        <div style={{ marginBottom: '5px', fontWeight: 'bold' }}>Filter:</div>
        <select 
          value={filter} 
          onChange={(e) => setFilter(e.target.value)}
          style={{ padding: '5px', borderRadius: '3px' }}
        >
          <option value="all">All ({filteredPlanes.length})</option>
          <option value="high">High Altitude (&gt;36k ft)</option>
          <option value="medium">Medium Altitude (30k-36k ft)</option>
          <option value="low">Low Altitude (&lt;30k ft)</option>
        </select>
      </div>

      {/* Stats Panel */}
      <div style={{
        position: 'absolute',
        left: '10px',
        bottom: '10px',
        zIndex: 1000,
        backgroundColor: 'white',
        padding: '10px',
        borderRadius: '4px',
        boxShadow: '0 1px 5px rgba(0,0,0,0.4)',
        fontSize: '12px',
      }}>
        <div><strong>Flights:</strong> {planes.length}</div>
        <div><strong>DRAP Points:</strong> {drapPoints.length}</div>
        {planesError && <div style={{ color: 'red' }}>Flight Error: {planesError}</div>}
        {drapError && <div style={{ color: 'red' }}>DRAP Error: {drapError}</div>}
      </div>

      {/* Dark Mode Toggle */}
      <button
        onClick={() => setDarkMode(!darkMode)}
        style={{
          position: 'absolute',
          right: '10px',
          top: '10px',
          zIndex: 1000,
          width: '30px',
          height: '45px',
          border: '2px solid rgba(0,0,0,0.2)',
          borderRadius: '4px',
          backgroundColor: 'white',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '18px',
          boxShadow: '0 1px 5px rgba(0,0,0,0.4)',
          transition: 'all 0.3s ease',
        }}
        title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = '#f4f4f4';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'white';
        }}
      >
        {darkMode ? '☀️' : '🌙'}
      </button>
    </div>
  );
};

export default PlaneTracker;