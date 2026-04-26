"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface MyRedemptionListItem {
  id: number;
  redemption_code: string;
  points_spent: number;
  status: "pending" | "used" | "expired";
  redeemed_at: string;
  expires_at: string;
  used_at: string | null;
  partner_id: number;
  partner_name: string;
  reward_id: number;
  reward_name: string;
  reward_image_url: string | null;
}

export interface MyRedemptionListResponse {
  items: MyRedemptionListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface MyRedemptionDetailResponse extends MyRedemptionListItem {
  snapshot_image_url: string | null;
  reward_description: string | null;
  reward_terms: string | null;
}

export function useMyRedemptions(status?: "pending" | "used" | "expired") {
  return useQuery<MyRedemptionListResponse>({
    queryKey: ["member", "redemptions", status ?? "all"],
    queryFn: async () => {
      const params = status ? `?status=${status}` : "";
      return (
        await api.get<MyRedemptionListResponse>(
          `/users/me/redemptions${params}`
        )
      ).data;
    },
  });
}

export function useMyRedemption(id: number) {
  return useQuery<MyRedemptionDetailResponse>({
    queryKey: ["member", "redemptions", id],
    queryFn: async () =>
      (await api.get<MyRedemptionDetailResponse>(`/users/me/redemptions/${id}`))
        .data,
    enabled: id > 0,
  });
}
