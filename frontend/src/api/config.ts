// API 공통 설정

import axios from 'axios';

export const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
