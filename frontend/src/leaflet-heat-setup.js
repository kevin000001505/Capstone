// This file must be imported BEFORE leaflet.heat
// It sets up the global L that leaflet.heat expects
import L from 'leaflet';

if (typeof window !== 'undefined') {
  window.L = L;
}
