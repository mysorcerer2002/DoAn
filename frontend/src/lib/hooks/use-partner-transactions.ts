"use client";

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { transactionsApi } from "@/lib/api-partner";
import type { TransactionUpdateRequest } from "@/types/partner";

export function usePartnerTransactions(params: {
  page: number;
  page_size: number;
  date_from?: string;
  date_to?: string;
  staff_id?: number;
  q?: string;
}) {
  return useQuery({
    queryKey: ["partner", "transactions", "list", params],
    queryFn: async () => (await transactionsApi.list(params)).data,
    placeholderData: keepPreviousData,
  });
}

export function usePartnerTransactionDetail(id: number | null) {
  return useQuery({
    queryKey: ["partner", "transaction", id],
    queryFn: async () => (await transactionsApi.get(id as number)).data,
    enabled: id !== null,
  });
}

export function useUpdatePartnerTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: TransactionUpdateRequest;
    }) => transactionsApi.update(id, payload).then((r) => r.data),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["partner", "transactions", "list"] });
      qc.invalidateQueries({ queryKey: ["partner", "transaction", vars.id] });
    },
  });
}
