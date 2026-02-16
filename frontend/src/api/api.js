import { createAsyncThunk } from "@reduxjs/toolkit";

const API_BASE_URL = '/api/v1';

export const fetchPlanes = createAsyncThunk(
  'planes/fetchPlanes',
  async (_, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/flight-states/latest`);
      if (!response.ok) {
        throw new Error('Failed to fetch flight data');
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchDRAP = createAsyncThunk(
  'drap/fetchDRAP',
  async (_, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/drap/latest`);
      if (!response.ok) {
        throw new Error('Failed to fetch DRAP data');
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);