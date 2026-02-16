import { configureStore } from '@reduxjs/toolkit';
import planesReducer from './slices/planesSlice';
import drapReducer from './slices/drapSlice';

export const store = configureStore({
  reducer: {
    planes: planesReducer,
    drap: drapReducer,
  },
});