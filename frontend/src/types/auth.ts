export interface User {
  id: number;
  email: string | null;
  phone: string | null;
  full_name: string | null;
  birthday: string | null;
  system_role: string;
  created_at: string;
}

export interface Membership {
  membership_id: number;
  tenant_id: number;
  user_id: number;
  user_phone: string | null;
  user_full_name: string | null;
  user_email: string | null;
  points_balance: number;
  total_points_earned: number;
  current_tier_id: number | null;
  current_tier_name: string | null;
  joined_at: string;
  last_activity_at: string | null;
  is_new: boolean;
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
}

export interface LoginRequest {
  email: string;
  password: string;
}
