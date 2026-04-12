export interface User {
  id: number;
  email: string | null;
  full_name: string | null;
  birthday: string | null;
  system_role: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  birthday?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}
